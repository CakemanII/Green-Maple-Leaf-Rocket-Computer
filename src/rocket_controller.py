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

Color = tuple[int, int, int]

class RocketController:
    SENSOR_VERIFY_ATTEMPT_DELAY = 0.1
    ITERATION_DELAY: float = 0.75

    def __init__(self):
        self._fans_pin = gpiozero.PWMOutputDevice(15)  # Example GPIO pin for fan control
        self._peizo_pin = gpiozero.PWMOutputDevice(18)  # Example GPIO pin for piezo buzzer control

        self._co2_breach_triggered = False
        self._peizo_is_active = False

        # I2C SETUP
        # Initialize the I2C bus using Raspberry Pi hardware pins (SCL/SDA)
        self._i2c = busio.I2C(board.SCL, board.SDA)

        # Give sensors time to power up and stabilize
        time.sleep(1.5)

        # Create LCD
        self._lcd = LCDController()

        # Alert to not move the rocket computer during sensor initialization and calibration
        self._lcd.clear()
        self._lcd.clear_emotion()
        for _ in range(8):
            self._lcd.screen_off()
            time.sleep(0.15)
            self._lcd.screen_on()
            time.sleep(0.15)
        self._lcd.print_line("IMU Calibrating", 0)
        self._lcd.print_line("Keep Still!!!", 1)
        
        # Setup the IMU
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
        for _ in range(2):
            time.sleep(0.5)
            self._lcd.print_line("All Sensors", 0)
            self._lcd.print_line("Calibrated!", 1)
            self._lcd.print_emotion(LCDController.SMILEY_FACE, 13)
            time.sleep(0.5)
            self._lcd.clear()
            self._lcd.clear_emotion()


    def is_co2_breach_triggered(self) -> bool: return self._co2_breach_triggered

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