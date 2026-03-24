import board
import busio
import serial
import gpiozero
import time

from datetime import datetime

import pynmea2
import adafruit_dps310
from adafruit_bno08x.i2c import BNO08X_I2C
from adafruit_bno08x import (
    BNO_REPORT_ACCELEROMETER,
    BNO_REPORT_GYROSCOPE,
    BNO_REPORT_MAGNETOMETER,
)

Color = tuple[int, int, int]

class RocketController:
    DISPLAY_DIAGNOSTIC: list[tuple[float, Color]] = [
        [1, Color(255, 0, 0)],    # Red
        [2, Color(255, 165, 0)],  # Orange
        [3, Color(255, 255, 0)],  # Yellow
        [4, Color(0, 128, 0)],    # Green
        [5, Color(0, 0, 255)],    # Blue
        [6, Color(75, 0, 130)],   # Indigo
        [7, Color(238, 130, 238)],# Violet
        [8, Color(255, 255, 255)] # White
    ]
    SENSOR_VERIFY_ATTEMPT_DELAY = 0.1
    ITERATION_DELAY: float = 0.75

    def __init__(self):
        self._accel_offset = None
        self._gyro_offset = None

        self._co2_breach_triggered = False
        self._peizo_is_active = False
        self._led_is_active = False

        # I2C SETUP
        # Initialize the I2C bus using Raspberry Pi hardware pins (SCL/SDA)
        self._i2c = busio.I2C(board.SCL, board.SDA)

        # Give sensors time to power up and stabilize
        time.sleep(1.5)

        # Sensor Setup
        self._verify_dps_device()
        self._setup_gps_device()
        self._verify_imu_device()

        # Calibrate the IMU (this can take a few seconds)
        print("Calibrating IMU... Please keep the device still.")
        self._calibrate_imu()
        print("IMU calibration complete.")

        # Manually verify LED and piezo devices (play sounds and light up for a few seconds.)
        self._diagnose_led_and_piezo_device()

    def is_co2_breach_triggered(self) -> bool: return self._co2_breach_triggered

    # region Sensor Setup
    def _verify_dps_device(self):
        while True:
            try:
                # Initialize DPS310 pressure/temperature sensor
                self._dps = adafruit_dps310.DPS310(self._i2c)
                # Set reference sea-level pressure for altitude calculation
                self._dps.sea_level_pressure = 1013.25
                # Verify sensor is responding by reading a value
                _ = self._dps.pressure
                print("DPS310 sensor initialized successfully")
                break
            except:
                print(f"DPS310 sensor initialization failed. Retrying in {RocketController.SENSOR_VERIFY_ATTEMPT_DELAY} seconds...")
                time.sleep(RocketController.SENSOR_VERIFY_ATTEMPT_DELAY)

    def _setup_gps_device(self):
        # Serial port used by the GPS module
        PORT = "/dev/ttyAMA0"
        BAUD = 9600

        # Open serial connection to GPS
        self._ser = serial.Serial(PORT, BAUD, timeout=1)

    def _verify_imu_device(self):
        while True:
            try:
                # Create BNO08X IMU object
                self._bno = BNO08X_I2C(self._i2c)

                self._bno.enable_feature(BNO_REPORT_ACCELEROMETER)
                self._bno.enable_feature(BNO_REPORT_GYROSCOPE)
                self._bno.enable_feature(BNO_REPORT_MAGNETOMETER)

                # Verify sensor is responding by reading a value
                _ = self._bno.acceleration
                _ = self._bno.gyro
                _ = self._bno.magnetic
                print("BNO08X IMU initialized successfully")
                break
            except:
                print(f"BNO08X IMU initialization failed. Retrying in {RocketController.SENSOR_VERIFY_ATTEMPT_DELAY} seconds...")
                time.sleep(RocketController.SENSOR_VERIFY_ATTEMPT_DELAY)
                continue
    
    def _diagnose_led_and_piezo_device(self):
        """
        Run the LED and piezo buzzer through a simple test pattern to verify they are working.
        """
        # Run the LED and piezo buzzer through a simple test pattern to verify they are working.
        # SO, RE, MI, FA, SOL, LA, TI, DO
        # RED, ORANGE, YELLOW, GREEN, BLUE, INDIGO, VIOLET, WHITE
        for pitch, color in RocketController.DISPLAY_DIAGNOSTIC + reversed(RocketController.DISPLAY_DIAGNOSTIC):
            self.set_led_active(color)
            self.set_peizo_active(pitch)
            time.sleep(RocketController.ITERATION_DELAY)
            self.set_peizo_active(0.0)
    # endregion

    def _calibrate_imu(self):
        # Number of samples used to compute calibration offsets
        SAMPLES = 400

        # Accumulators for accelerometer and gyroscope readings
        ax = ay = az = 0.0
        gx = gy = gz = 0.0

        # Collect samples while the sensor is stationary
        for _ in range(SAMPLES):
            a = self._bno.acceleration  # Acceleration in m/s²
            g = self._bno.gyro          # Angular velocity in rad/s

            ax += a[0]
            ay += a[1]
            az += a[2]

            gx += g[0]
            gy += g[1]
            gz += g[2]

            # Small delay to control sampling rate
            time.sleep(0.005)

        # Compute average accelerometer offsets
        # Z-axis offset removes gravity (9.80665 m/s²)
        self._accel_offset = (
            ax / SAMPLES,
            ay / SAMPLES,
            (az / SAMPLES) - 9.80665
        )

        # Compute average gyroscope offsets (drift)
        self._gyro_offset = (
            gx / SAMPLES,
            gy / SAMPLES,
            gz / SAMPLES
        )

        print("IMU calibrated")
    # endregion

    # region Sensor Data Retrieval
    def get_gps_sensor_data(self) -> object:
        """
        Get the GPS sensor data.
        """
        # Read one NMEA sentence from the GPS
        line = self._ser.readline().decode("ascii", errors="replace")

        # Process GPGGA sentences (contain fix data)
        if line.startswith("$GPGGA"):
            msg = pynmea2.parse(line)

            latitude = msg.latitude
            longitude = msg.longitude
            altitude = msg.altitude
            timestamp = msg.timestamp

            return {
                "latitude": latitude,
                "longitude": longitude,
                "altitude": altitude,
                "timestamp": timestamp,
            }

    def get_dps_sensor_data(self) -> object:
        """
        Get the DPS sensor data.
        """
        pressure = self._dps.pressure
        altitude = self._dps.altitude
        temperature = self._dps.temperature
        return {
            "pressure": pressure,
            "altitude": altitude,
            "temperature": temperature
        }

    def get_imu_sensor_data(self) -> object:
        """
        Get the IMU sensor data.
        """
        # Read raw sensor data from the BNO08X
        ax, ay, az = self._bno.acceleration
        gx, gy, gz = self._bno.gyro
        mx, my, mz = self._bno.magnetic

        # Apply calibration offsets to raw sensor data
        ax -= self._accel_offset[0]
        ay -= self._accel_offset[1]
        az -= self._accel_offset[2]

        gx -= self._gyro_offset[0]
        gy -= self._gyro_offset[1]
        gz -= self._gyro_offset[2]

        return {
            "acceleration": (ax, ay, az),
            "gyroscope": (gx, gy, gz),
            "magnetometer": (mx, my, mz),
        }
    #endregion

    def set_peizo_active(self, state: float | None):
        """
        Set the piezo buzzer state.
        """        
        pass
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