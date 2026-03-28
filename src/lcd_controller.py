from RPLCD.i2c import CharLCD
import time
 
class LCDController:
    SMILEY_FACE = {
        "top_left": (
            0b00111,
            0b01111,
            0b11000,
            0b10011,
            0b10011,
            0b11000,
            0b01111,
            0b00111,
        ),

        "top_right": (
            0b11100,
            0b11110,
            0b00011,
            0b11001,
            0b11001,
            0b00011,
            0b11110,
            0b11100,
        ),

        "bot_left": (
            0b11000,
            0b10001,
            0b10001,
            0b01001,
            0b00111,
            0b00011,
            0b01111,
            0b00111,
        ),
        
        "bot_right": (
            0b00011,
            0b10001,
            0b10001,
            0b10010,
            0b11100,
            0b11000,
            0b11110,
            0b11100,
        )
    }

    def __init__(self):
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
 
    def print_line(self, text, row=0, align="left"):
        """Print text on a full line with optional alignment."""
        text = text[:16]
        if align == "center":
            text = text.center(16)
        elif align == "right":
            text = text.rjust(16)
        else:
            text = text.ljust(16)
        self._lcd.cursor_pos = (row, 0)
        self._lcd.write_string(text)
 
    def scroll_text(self, text, row=1, delay=0.3, scroll_right_to_left=True):
        """Scroll a long string across one row in either direction."""
        padded = " " * 16 + text + " " * 16
        if scroll_right_to_left:
            indices = range(len(padded) - 15)
        else:
            indices = range(len(padded) - 16, -1, -1)

        for i in indices:
            self._lcd.cursor_pos = (row, 0)
            self._lcd.write_string(padded[i:i + 16])
            time.sleep(delay) 

    def print_smiley_face(self):
        """Print a smiley face using custom characters."""
        # Create custom characters for the smiley face
        self._lcd.create_char(0, self.SMILEY_FACE["top_left"])
        self._lcd.create_char(1, self.SMILEY_FACE["top_right"])
        self._lcd.create_char(2, self.SMILEY_FACE["bot_left"])
        self._lcd.create_char(3, self.SMILEY_FACE["bot_right"])

        # Print the smiley face using the custom characters
        self._lcd.cursor_pos = (0, 5)
        self._lcd.write_string(chr(0) + chr(1))
        self._lcd.cursor_pos = (1, 5)
        self._lcd.write_string(chr(2) + chr(3))

    def clear(self):
        """Clear the LCD display."""
        self._lcd.clear()

    def screen_on(self):
        """Turn on the LCD backlight."""
        self._lcd.backlight_enabled = True

    def screen_off(self):
        """Turn off the LCD backlight."""
        self._lcd.backlight_enabled = False

lcd_controller = LCDController()
lcd_controller.print_smiley_face()