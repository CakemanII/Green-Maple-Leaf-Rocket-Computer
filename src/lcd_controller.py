from RPLCD.i2c import CharLCD
import time
 
class LCDController:
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
 
    def scroll_text(self, text, row=1, delay=0.3):
        """Scroll a long string across one row."""
        padded = " " * 16 + text + " " * 16
        for i in range(len(padded) - 15):
            self._lcd.cursor_pos = (row, 0)
            self._lcd.write_string(padded[i:i + 16])
            time.sleep(delay)
 
 
    def print_vertical(self, text, delay=0.6):
        """Display text vertically, 2 characters at a time."""
        text = text.upper()
        for i in range(0, len(text), 2):
            self._lcd.clear()
            self.print_line(text[i], row=0, align="center")
            self.print_line(text[i + 1] if i + 1 < len(text) else " ", row=1, align="center")
            time.sleep(delay)
 

    def clear(self):
        """Clear the LCD display."""
        self._lcd.clear()

    def backlight_on(self):
        """Turn on the LCD backlight."""
        self._lcd.backlight_enabled = True

    def backlight_off(self):
        """Turn off the LCD backlight."""
        self._lcd.backlight_enabled = False

lcd = LCDController()
lcd.print_line("Hello, World!", align="center")
time.sleep(1)
lcd.scroll_text("Welcome to the Rocket Computer! "*5, delay=0.1)
time.sleep(1)
lcd.print_vertical("Rocket Computer", delay=0.5)