import board
import busio
import serial
import gpiozero
import time

from datetime import datetime

import pynmea2
import adafruit_dps310
import smbus2
from adafruit_bno08x.i2c import BNO08X_I2C
from adafruit_bno08x import (
    BNO_REPORT_ACCELEROMETER,
    BNO_REPORT_GYROSCOPE,
    BNO_REPORT_MAGNETOMETER,
)

class RocketController:
    SENSOR_VERIFY_ATTEMPT_DELAY = 0.2

    def __init__(self):
        self._fans_pin = gpiozero.PWMOutputDevice(15)  # Example GPIO pin for fan control
        self._peizo_pin = gpiozero.PWMOutputDevice(18)  # Example GPIO pin for piezo buzzer control

        self._accel_offset = None
        self._gyro_offset = None

        self._co2_breach_triggered = False

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
    
    def _verify_camera_device(self):
        pass
    # endregion

    # region Fan Setup
    def _verify_fan_device(self):
        pass
    # endregion

    # region Display Setup

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

    # region LCD Screen Control
    def set_lcd_display(self, message: str):
        """
        Update the LCD display with the provided data.
        """
        pass
    # endregion

    # region Fan Control
    def set_fan_rpm(self, rpm_percentage: float):
        """
        Set the fan speed as a percentage of maximum RPM.
        """
        pass
    # endregion

    # region Peizo Buzzer Control
    def play_buzzer_tone(self, frequency: float, duration: float = None):
        """
        Play a tone on the piezo buzzer at the specified frequency and duration.
        """
        pass

    def stop_buzzer_tone(self):
        """
        Stop any currently playing tone on the piezo buzzer.
        """
        pass
    

    def toggle_rocket_camera_state(self, state: bool):
        """
        Toggle the rocket camera state.
        """
        pass

    def breach_co2_canister(self):
        """
        Rotate the servo and breach the CO2 canister.
        """
        # Breach the co2
        # ...

        # Set the flag
        self._co2_breach_triggered = True

