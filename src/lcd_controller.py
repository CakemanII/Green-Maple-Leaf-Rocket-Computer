from RPLCD.i2c import CharLCD
import time
 
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
        self._emotion_visible = False
        self._emotion_position = None
        self._verify_lcd_device()

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
                print("LCD initialized successfully")
                break
            except Exception as e:
                print(f"LCD initialization failed: {e}. Retrying in 0.5 seconds...")
                time.sleep(0.5)

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
 
    def print_line(self, text, row=0, align="left", avoid_overlapping_emotion=True):
        """Print text on a full line with optional alignment."""
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
 
    def scroll_text(self, text, row=1, delay=0.3, scroll_right_to_left=True, avoid_overlapping_emotion=True):
        """Scroll a long string across one row in either direction."""
        padded = " " * 16 + text + " " * 16
        if scroll_right_to_left:
            indices = range(len(padded) - 15)
        else:
            indices = range(len(padded) - 16, -1, -1)

        for i in indices:
            visible_text = padded[i:i + 16]
            visible_text = self._apply_emotion_overlay(visible_text, row, avoid_overlapping_emotion)
            self._lcd.cursor_pos = (row, 0)
            self._lcd.write_string(visible_text)
            time.sleep(delay) 

    def print_emotion(self, emotion: EMOTION, horizontal_position=0):
        # Clear the previous emotion if it exists
        if self._emotion_visible and self._emotion_position is not None:
            for i in range(6):
                self._lcd.create_char(i, [0b00000] * 8)

        """Print an emotion using custom characters."""
        # Create custom characters for the emotion
        for i, bitmap in enumerate(emotion):
            self._lcd.create_char(i, bitmap)

        # Print the emotion using the custom characters
        self._lcd.cursor_pos = (0, horizontal_position)
        self._lcd.write_string(chr(0) + chr(1) + chr(2))
        self._lcd.cursor_pos = (1, horizontal_position)
        self._lcd.write_string(chr(3) + chr(4) + chr(5))

        # Set variables
        self._emotion_visible = True
        self._emotion_position = horizontal_position

    def clear(self):
        """Clear the LCD display."""
        self._lcd.clear()

        # Reset emotion state
        self._emotion_visible = False
        self._emotion_position = None

    def screen_on(self):
        """Turn on the LCD backlight."""
        self._lcd.backlight_enabled = True

    def screen_off(self):
        """Turn off the LCD backlight."""
        self._lcd.backlight_enabled = False

lcd_controller = LCDController()
for _ in range(3):
    lcd_controller.print_emotion(LCDController.SMILEY_FACE, horizontal_position=5)
    time.sleep(1)
    lcd_controller.print_emotion(LCDController.SAD_FACE, horizontal_position=5)
    time.sleep(1)
    lcd_controller.print_emotion(LCDController.ANGRY_FACE, horizontal_position=5)
    time.sleep(1)
lcd_controller.scroll_text("Hello, World!"*2, row=1, delay=0.25)