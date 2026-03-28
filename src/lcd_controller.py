from RPLCD.i2c import CharLCD
import time
import threading
import queue
import math
 
EMOTION = list[tuple[int, int, int, int, int, int, int, int]]

class LCDController:
    # Custom character bitmaps for smiley face
    SMILEY_FACE = [
        (0b00001, 0b00011, 0b00111, 0b01110, 0b11110, 0b11111, 0b11111, 0b11111),
        (0b11111, 0b11111, 0b11111, 0b01110, 0b01110, 0b11111, 0b11111, 0b11111),
        (0b10000, 0b11000, 0b11100, 0b01110, 0b01111, 0b11111, 0b11111, 0b11111),
        (0b11011, 0b11000, 0b11100, 0b11110, 0b01111, 0b00111, 0b00011, 0b00001),
        (0b11111, 0b00000, 0b00000, 0b00000, 0b00000, 0b11111, 0b11111, 0b11111),
        (0b11011, 0b00011, 0b00111, 0b01111, 0b11110, 0b11100, 0b11000, 0b10000)
   ]
    
    SAD_FACE = [
        (0b00001, 0b00011, 0b00111, 0b01110, 0b11100, 0b11111, 0b11111, 0b11111),
        (0b11111, 0b11111, 0b11111, 0b01110, 0b00100, 0b11111, 0b11111, 0b11111),
        (0b10000, 0b11000, 0b11100, 0b01110, 0b00111, 0b11111, 0b11111, 0b11111),
        (0b11111, 0b11111, 0b11110, 0b11100, 0b01101, 0b00111, 0b00011, 0b00001),
        (0b11111, 0b00000, 0b00000, 0b11111, 0b11111, 0b11111, 0b11111, 0b11111),
        (0b11111, 0b11111, 0b01111, 0b00111, 0b10110, 0b11100, 0b11000, 0b10000)
    ]

    ANGRY_FACE = [
        (0b00011, 0b00111, 0b00111, 0b01110, 0b11110, 0b11111, 0b11111, 0b11111),
        (0b11111, 0b11111, 0b11111, 0b11111, 0b01110, 0b00100, 0b11111, 0b11111),
        (0b10000, 0b11000, 0b11100, 0b01110, 0b01111, 0b11111, 0b11111, 0b11111),
        (0b11111, 0b11111, 0b11111, 0b11110, 0b01111, 0b00111, 0b00011, 0b00000),
        (0b11111, 0b11111, 0b00000, 0b11111, 0b11111, 0b11111, 0b11111, 0b00000),
        (0b11111, 0b11111, 0b11111, 0b01111, 0b11110, 0b11100, 0b11000, 0b00000)
    ]

    def __init__(self):
        self._lcd = None
        self._emotion_visible = False
        self._emotion_position = None
        self._current_emotion = None
        self._lcd_lock = threading.Lock()
        self._command_queue = queue.Queue()
        self._running = True

        # Live scrolling state (per row: 0 and 1)
        self._live_scroll_active = {0: False, 1: False}
        self._live_scroll_text = {0: "", 1: ""}
        self._live_scroll_index = {0: 0, 1: 0}
        self._live_scroll_delay = {0: 0.3, 1: 0.3}
        self._live_scroll_direction = {0: True, 1: True}  # True = right_to_left
        self._live_scroll_avoid_emotion = {0: True, 1: True}
        self._live_scroll_padded = {0: "", 1: ""}
        self._live_scroll_last_frame = {0: 0.0, 1: 0.0}

        # Start worker thread (will initialize LCD in background)
        self._worker_thread = threading.Thread(target=self._main, daemon=True)
        self._worker_thread.start()

    def _verify_lcd_device(self):
        while True:
            try:
                # Set the LCD I2C object
                self._lcd = CharLCD(
                    i2c_expander='PCF8574',
                    address=0x27,
                    port=1,
                    cols=16,
                    rows=2,
                    charmap='A02',
                    auto_linebreaks=True
                )
                time.sleep(0.5)
                # Hide the blinking cursor for cleaner display
                self._lcd.cursor = False
                self._lcd.blink = False
                self._do_clear()  # Clear the display on startup
                print("LCD initialized successfully")
                break
            except Exception as e:
                print(f"LCD initialization failed: {e}. Retrying in 0.5 seconds...")
                time.sleep(0.5)

    def _main(self):
        """Worker thread that initializes LCD and processes commands from the queue."""
        # Initialize LCD on worker thread (non-blocking to caller)
        self._verify_lcd_device()

        # Process commands
        while self._running:
            # Process queued commands (non-blocking)
            try:
                command = self._command_queue.get(timeout=0.01)
                cmd_type, args = command

                if cmd_type == "print_line":
                    self._do_print_line(*args)
                elif cmd_type == "scroll_text":
                    self._do_scroll_text(*args)
                elif cmd_type == "set_live_scrolling_text":
                    self._do_set_live_scrolling_text(*args)
                elif cmd_type == "print_emotion":
                    self._do_print_emotion(*args)
                elif cmd_type == "clear_emotion":
                    self._do_clear_emotion()
                elif cmd_type == "clear":
                    self._do_clear()
                elif cmd_type == "screen_on":
                    self._do_screen_on()
                elif cmd_type == "screen_off":
                    self._do_screen_off()
            except queue.Empty:
                pass

            # Handle live scrolling if active on any row (only if LCD is ready)
            if self._lcd:
                current_time = time.time()
                # Render row 0 if active and timing is due
                if self._live_scroll_active.get(0, False):
                    if current_time - self._live_scroll_last_frame.get(0, 0) >= self._live_scroll_delay.get(0, 0.3):
                        self._do_live_scroll_frame(0)
                        self._live_scroll_last_frame[0] = current_time
                # Render row 1 if active and timing is due
                if self._live_scroll_active.get(1, False):
                    if current_time - self._live_scroll_last_frame.get(1, 0) >= self._live_scroll_delay.get(1, 0.3):
                        self._do_live_scroll_frame(1)
                        self._live_scroll_last_frame[1] = current_time

            time.sleep(0.01)  # Small sleep to avoid busy waiting

    # region Actual Controller Functions
    def _do_print_line(self, text, row, align, avoid_overlapping_emotion):
        """Internal: Execute print_line command. Skipped if live scrolling is active on this row."""
        if self._live_scroll_active.get(row, False):
            return  # Don't override live scrolling

        with self._lcd_lock:
            text = text[:16]
            if align == "center":
                text = text.center(16)
            elif align == "right":
                text = text.rjust(16)
            else:
                text = text.ljust(16)
            text = self._apply_emotion_overlay(text, row, avoid_overlapping_emotion)
            self._lcd.cursor_pos = (row, 0)
            self._lcd.write_string(text)

    def _do_scroll_text(self, text, row, delay, scroll_right_to_left, avoid_overlapping_emotion):
        """Internal: Execute scroll_text command. Skipped if live scrolling is active on this row."""
        if self._live_scroll_active.get(row, False):
            return  # Don't override live scrolling

        padded = " " * 16 + text + " " * 16
        if scroll_right_to_left:
            indices = range(len(padded) - 15)
        else:
            indices = range(len(padded) - 16, -1, -1)

        for i in indices:
            if self._live_scroll_active.get(row, False):
                return  # Stop if live scrolling started

            with self._lcd_lock:
                visible_text = padded[i:i + 16]
                visible_text = self._apply_emotion_overlay(visible_text, row, avoid_overlapping_emotion)
                self._lcd.cursor_pos = (row, 0)
                self._lcd.write_string(visible_text)
            time.sleep(delay)

    def _do_set_live_scrolling_text(self, text, row, delay, scroll_right_to_left, avoid_overlapping_emotion, enabled, seamless_wrap):
        """Internal: Set or disable live scrolling text."""
        if not enabled:
            self._live_scroll_active[row] = False
            return

        was_active = self._live_scroll_active.get(row, False)
        previous_index = self._live_scroll_index.get(row, 0)

        # Setup live scrolling for this row
        self._live_scroll_text[row] = text
        self._live_scroll_delay[row] = delay
        self._live_scroll_direction[row] = scroll_right_to_left
        self._live_scroll_avoid_emotion[row] = avoid_overlapping_emotion
        
        # Create padded or repeated text - MUST be at least 32 chars for safe slicing
        if seamless_wrap and text:
            # Repeat text to create seamless wrapping
            # Calculate how many times to repeat so total length is at least 64 chars (64-16=48 valid indices)
            repeat_count = max(2, math.ceil(64 / len(text)))
            self._live_scroll_padded[row] = text * repeat_count
        else:
            # Original padding approach with spaces
            # Guarantees at least 48 chars: 16 + text + 16 = at least 32 (if text is 0), typically much more
            self._live_scroll_padded[row] = " " * 16 + text + " " * 16
        
        # Ensure minimum 32 chars for safety
        if len(self._live_scroll_padded[row]) < 32:
            self._live_scroll_padded[row] = (self._live_scroll_padded[row] + " " * 32)[:32]
        
        max_index = max(0, len(self._live_scroll_padded[row]) - 16)

        # Preserve scroll position when already active, even if text is updated.
        if was_active:
            self._live_scroll_index[row] = previous_index % (max_index + 1)
        else:
            if scroll_right_to_left:
                self._live_scroll_index[row] = 0
            else:
                self._live_scroll_index[row] = max_index

        # Keep timing when already active so frequent updates do not stall motion.
        if not was_active:
            # Set to (now - delay) so first frame fires immediately.
            self._live_scroll_last_frame[row] = time.time() - delay

        self._live_scroll_active[row] = True

    def _do_live_scroll_frame(self, row):
        """Internal: Render one frame of live scrolling text for the specified row."""
        # Safety checks
        if not self._lcd:
            return  # LCD not initialized yet
        
        if not self._live_scroll_padded.get(row, ""):
            return  # No text to display
        
        padded_text = self._live_scroll_padded[row]
        if len(padded_text) < 16:
            return  # Padded text too short - shouldn't happen but safety check
        
        current_index = self._live_scroll_index[row]
        
        # Ensure index is within valid range
        if current_index < 0:
            current_index = 0
        if current_index > len(padded_text) - 16:
            current_index = 0
        
        with self._lcd_lock:
            # Get the 16-char window, ensuring we never return < 16 chars
            visible_text = padded_text[current_index:current_index + 16]
            # CRITICAL: Pad to exactly 16 chars to prevent display corruption
            visible_text = visible_text.ljust(16)
            
            # Apply emotion overlay (works safely with 16-char text)
            visible_text = self._apply_emotion_overlay(visible_text, row, self._live_scroll_avoid_emotion[row])
            
            # Write to LCD
            self._lcd.cursor_pos = (row, 0)
            self._lcd.write_string(visible_text)

        # Update index for next frame
        if self._live_scroll_direction[row]:  # right_to_left
            self._live_scroll_index[row] = current_index + 1
            if self._live_scroll_index[row] > len(padded_text) - 16:
                self._live_scroll_index[row] = 0
        else:  # left_to_right
            self._live_scroll_index[row] = current_index - 1
            if self._live_scroll_index[row] < 0:
                self._live_scroll_index[row] = len(padded_text) - 16

    def _do_print_emotion(self, emotion, horizontal_position):
        """Internal: Execute print_emotion command."""
        # Skip if this exact emotion is already displayed at this position
        if (self._current_emotion == emotion and 
            self._emotion_position == horizontal_position and 
            self._emotion_visible):
            return

        with self._lcd_lock:
            # Clear previous emotion glyphs if switching emotions
            if self._emotion_visible and self._current_emotion != emotion:
                old_pos = self._emotion_position if self._emotion_position is not None else 0
                self._lcd.cursor_pos = (0, old_pos)
                self._lcd.write_string("   ")  # Clear 3 chars on row 0
                self._lcd.cursor_pos = (1, old_pos)
                self._lcd.write_string("   ")  # Clear 3 chars on row 1
                time.sleep(0.02)

            # Load new emotion bitmaps
            for i, bitmap in enumerate(emotion):
                self._lcd.create_char(i, bitmap)
            time.sleep(0.05)  # Allow controller time to process

            # Print the emotion using the custom characters
            self._lcd.cursor_pos = (0, horizontal_position)
            self._lcd.write_string(chr(0) + chr(1) + chr(2))
            self._lcd.cursor_pos = (1, horizontal_position)
            self._lcd.write_string(chr(3) + chr(4) + chr(5))

            # Set variables
            self._emotion_visible = True
            self._emotion_position = horizontal_position
            self._current_emotion = emotion

    def _do_clear_emotion(self):
        """Internal: Execute clear_emotion command."""
        with self._lcd_lock:
            if self._emotion_visible and self._emotion_position is not None:
                pos = self._emotion_position
                self._lcd.cursor_pos = (0, pos)
                self._lcd.write_string("   ")  # Clear 3 chars on row 0
                self._lcd.cursor_pos = (1, pos)
                self._lcd.write_string("   ")  # Clear 3 chars on row 1
                time.sleep(0.02)

        # Reset emotion state
        self._emotion_visible = False
        self._emotion_position = None
        self._current_emotion = None

    def _do_clear(self):
        """Internal: Execute clear command."""
        with self._lcd_lock:
            self._lcd.clear()

        # Reset emotion state
        self._emotion_visible = False
        self._emotion_position = None
        self._current_emotion = None

    def _do_screen_on(self):
        """Internal: Execute screen_on command."""
        with self._lcd_lock:
            self._lcd.backlight_enabled = True

    def _do_screen_off(self):
        """Internal: Execute screen_off command."""
        with self._lcd_lock:
            self._lcd.backlight_enabled = False
    # endregion

    def _apply_emotion_overlay(self, text, row, avoid_overlapping_emotion):
        """Keep the emotion visible by restoring its glyphs on protected cells."""
        if not (avoid_overlapping_emotion and self._emotion_visible and self._emotion_position is not None):
            return text

        if row not in (0, 1):
            return text

        chars = list(text)
        base_char = 0 if row == 0 else 3
        for offset in range(3):
            col = self._emotion_position + offset
            if 0 <= col < 16:
                chars[col] = chr(base_char + offset)

        return "".join(chars)
    
    # region Task Functions
    def print_line(self, text, row=0, align="left", avoid_overlapping_emotion=True):
        """Queue a print_line command (non-blocking)."""
        self._command_queue.put(("print_line", (text, row, align, avoid_overlapping_emotion)))
 
    def scroll_text(self, text, row=1, delay=0.3, scroll_right_to_left=True, avoid_overlapping_emotion=True):
        """Queue a scroll_text command (non-blocking)."""
        self._command_queue.put(("scroll_text", (text, row, delay, scroll_right_to_left, avoid_overlapping_emotion)))

    def set_live_scrolling_text(self, text, row=1, delay=0.3, scroll_right_to_left=True, avoid_overlapping_emotion=True, enabled=True, seamless_wrap=True):
        """Queue a set_live_scrolling_text command (non-blocking). 
        
        When enabled, turns on live scrolling that can be updated without resetting position.
        Live scrolling cannot be overridden by other text commands (except emotion if avoid is off).
        
        seamless_wrap: If True, repeats text seamlessly (e.g., "Hi! " loops as "Hi! Hi! Hi! ...")
                       instead of padding with spaces. No gaps when wrapping.
        Pass enabled=False to stop live scrolling.
        """
        self._command_queue.put(("set_live_scrolling_text", (text, row, delay, scroll_right_to_left, avoid_overlapping_emotion, enabled, seamless_wrap)))

    def print_emotion(self, emotion: EMOTION, horizontal_position=0):
        """Queue a print_emotion command (non-blocking)."""
        self._command_queue.put(("print_emotion", (emotion, horizontal_position)))

    def clear_emotion(self):
        """Queue a clear_emotion command (non-blocking)."""
        self._command_queue.put(("clear_emotion", ()))

    def clear(self):
        """Queue a clear command (non-blocking)."""
        self._command_queue.put(("clear", ()))

    def screen_on(self):
        """Queue a screen_on command (non-blocking)."""
        self._command_queue.put(("screen_on", ()))

    def screen_off(self):
        """Queue a screen_off command (non-blocking)."""
        self._command_queue.put(("screen_off", ()))

    def stop(self):
        """Stop the worker thread (graceful shutdown)."""
        self._running = False
        if self._worker_thread.is_alive():
            self._worker_thread.join(timeout=1.0)
    # endregion