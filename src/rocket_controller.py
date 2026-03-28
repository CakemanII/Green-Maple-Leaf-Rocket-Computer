import board
import busio
import serial
import gpiozero
import time
from datetime import datetime

from imu_controller import IMUSensorController
from dps_controller import DPSSensorController
from gps_controller import GPSSensorController
from lcd_controller import LCDController
from piezo_controller import PiezoController

Color = tuple[int, int, int]

class RocketController:
    SENSOR_VERIFY_ATTEMPT_DELAY = 0.1
    ITERATION_DELAY: float = 0.75

    def __init__(self):
        self._co2_breach_triggered = False

        # I2C SETUP
        # Initialize the I2C bus using Raspberry Pi hardware pins (SCL/SDA)
        self._i2c = busio.I2C(board.SCL, board.SDA)

        # Give sensors time to power up and stabilize
        time.sleep(1.5)

        # Create LCD
        self._piezo = PiezoController()
        self._lcd = LCDController()

        # Blink the LCD backlight a few times to indicate startup
        for _ in range(8):
            self._lcd.screen_off()
            time.sleep(0.15)
            self._lcd.screen_on()
            time.sleep(0.15)

        # Play the piezo buzzer to indicate startup
        self._lcd.print_line("Playing Piezo", 0)
        self._lcd.print_line("You should hear it!", 1)
        self.play_alert_tone()

        # Setup the IMU
        self._lcd.print_line("IMU Calibrating", 0)
        self._lcd.print_line("Keep Still!!!", 1)
        
        time.sleep(0.25)
        self._bno = IMUSensorController(self._i2c)
        
        # Setup the GPS
        time.sleep(0.25)
        self._lcd.print_line("GPS Initializing", 0)
        self._lcd.print_line("Please Wait...", 1)
        self._gps = GPSSensorController(self._i2c)

        # Setup the DPS
        time.sleep(0.25)
        self._lcd.print_line("DPS Initializing", 0)
        self._lcd.print_line("Please Wait...", 1)
        self._dps = DPSSensorController(self._i2c)

        # Alert everything has been initialized and calibrated
        self._lcd.clear()
        self._lcd.print_line("All Sensors", 0)
        self._lcd.print_line("Calibrated!", 1)
        self._lcd.print_emotion(LCDController.SMILEY_FACE, 13)
        time.sleep(2)
        self._lcd.clear()
        self._lcd.clear_emotion()


    def is_co2_breach_triggered(self) -> bool: return self._co2_breach_triggered

    def play_startup_fanfare(self):
        """Play a cool startup jingle with the piezo buzzer."""
        # Define the melody: (frequency in Hz, duration in seconds)
        # This is a catchy sci-fi startup tune
        melody = [
            (523, 0.15),   # C5 - High note
            (587, 0.15),   # D5
            (659, 0.15),   # E5
            (784, 0.3),    # G5 - Hold
            (659, 0.15),   # E5
            (523, 0.15),   # C5
            (587, 0.45),   # D5 - Hold longer
            (0, 0.1),      # Silence
            (784, 0.2),    # G5
            (880, 0.2),    # A5
            (987, 0.4),    # B5 - High finish
            (880, 0.2),    # A5
            (784, 0.6),    # G5 - Fade to end
        ]
        
        for frequency, duration in melody:
            if frequency == 0:
                self._piezo.stop_buzzer()
            else:
                self._piezo.set_buzzer(frequency, 80)  # 80% volume
            time.sleep(duration)
        
        self._piezo.stop_buzzer()

    def play_alert_tone(self):
        """Play an urgent alert/warning tone."""
        alert_pattern = [
            (880, 0.1),    # A5 - High alert note
            (0, 0.05),     # Silence
            (880, 0.1),    # A5
            (0, 0.05),     # Silence
            (1047, 0.15),  # C6 - Even higher
            (0, 0.2),      # Longer silence
        ]
        
        for frequency, duration in alert_pattern:
            if frequency == 0:
                self._piezo.stop_buzzer()
            else:
                self._piezo.set_buzzer(frequency, 100)  # Full volume
            time.sleep(duration)
        
        self._piezo.stop_buzzer()

    def play_success_chime(self):
        """Play a pleasant success/confirmation chime."""
        chime = [
            (523, 0.2),    # C5
            (0, 0.05),
            (659, 0.2),    # E5
            (0, 0.05),
            (784, 0.4),    # G5 - Hold for success
            (0, 0.1),
            (784, 0.2),    # G5 again
        ]
        
        for frequency, duration in chime:
            if frequency == 0:
                self._piezo.stop_buzzer()
            else:
                self._piezo.set_buzzer(frequency, 75)
            time.sleep(duration)
        
        self._piezo.stop_buzzer()

    # region Fan Setup
    def _verify_fan_device(self):
        pass
    # endregion

    def set_peizo_active(self, state: float | None):
        """
        Set the piezo buzzer state.
        """        
        # Turn on or off the piezo buzzer based on the state parameter
        # ...

        # Set the flag
        self._peizo_is_active = state is not None

    def set_led_active(self, state: Color | None):
        """
        Set the LED to be off or on.
        """
        # Turn off or on the LED
        if state is None:
            # Turn off the LED
            # ...
            pass
        else:
            # Turn on the LED with the specified color
            # ...
            pass

        # Set the flag
        self._led_is_active = state is not None

    def toggle_rocket_camera_state(self, state: bool):
        """
        Toggle the rocket camera state.
        """
        pass
        # Toggle the camera on or off based on the state parameter
        # ...
    
    def breach_co2_canister(self):
        """
        Rotate the servo and breach the CO2 canister.
        """
        # Breach the co2
        # ...

        # Set the flag
        self._co2_breach_triggered = True

    # region Sensor Data Retrieval
    def get_dps_sensor_data(self) -> object | None: return self._dps.get_sensor_data()
    def get_gps_sensor_data(self) -> object | None: return self._gps.get_sensor_data()
    def get_imu_sensor_data(self) -> object | None: return self._bno.get_sensor_data()
    # endregion