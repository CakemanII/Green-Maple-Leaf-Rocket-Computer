import threading

import board
import busio
import serial
import gpiozero
import time
from datetime import datetime

from raspi_controller import RaspiController
from imu_controller import IMUSensorController
from dps_controller import DPSSensorController
from gps_controller import GPSSensorController
from lcd_controller import LCDController
from piezo_controller import PiezoController, PresetMusicalTones
from servo_controller import ServoController
from fans_controller import FansController


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

        # Create Raspi Controller
        self._raspi_controller = RaspiController()

        # Create LCD
        self._piezo = PiezoController()
        self._lcd = LCDController()

        # Create Servo Controllers
        self._servo_controller_1 = ServoController(pin=23)
        self._servo_controller_2 = ServoController(pin=24)

        # Create Fan Controllers
        self._fan_controller = FansController(gpio=16)

        # Blink the LCD backlight a few times to indicate startup
        for _ in range(1):
            self._lcd.screen_off()
            time.sleep(0.15)
            self._lcd.screen_on()
            time.sleep(0.15)

        # Testing Fans
        self._lcd.print_line("Testing Fans", 0)
        self._lcd.print_line("Fan should be ON", 1)

        for i in range(0, 101, 10):
            self._fan_controller.set_fan_speed(i)
            time.sleep(0.5)

        self._fan_controller.set_fan_speed(0)

        # Testing Servo
        self._lcd.print_line("Testing Servo", 0)
        self._lcd.print_line("Servo should be moving", 1)
        positions = [0, 45, 90, 180, 90, 45, 0]
        for pos in positions:
            self._servo_controller_1.set_servo_angle(pos)
            self._servo_controller_2.set_servo_angle(pos)

        # Play the piezo buzzer to indicate startup
        self._lcd.print_line("Playing Piezo", 0)
        self._lcd.print_line("You should hear it!", 1)
        #self._piezo.play_tone(PresetMusicalTones.VERIFICATION_TONE, threaded=False)

        # Setup the IMU
        self._lcd.print_line("IMU Calibrating", 0)
        self._lcd.print_line("Keep Still!!!", 1)
        
        time.sleep(0.25)
        self._imu = IMUSensorController(self._i2c)
        
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

    # region Fan Setup
    def _verify_fan_device(self):
        pass
    # endregion

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
    def get_imu_sensor_data(self) -> object | None: return self._imu.get_sensor_data()
    def get_raspi_stats(self) -> object | None: return self._raspi_controller.get_raspi_stats()
    # endregion