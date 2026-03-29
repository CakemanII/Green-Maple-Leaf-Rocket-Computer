import math

from adafruit_bno08x.i2c import BNO08X_I2C
from adafruit_bno08x import (
    BNO_REPORT_ACCELEROMETER,
    BNO_REPORT_GYROSCOPE,
    BNO_REPORT_MAGNETOMETER,
    BNO_REPORT_ROTATION_VECTOR,
    BNO_REPORT_LINEAR_ACCELERATION,
    BNO_REPORT_GRAVITY
)
from sensor_controller import SensorController

import time

class IMUSensorController(SensorController):
    CALIBRATION_SAMPLES = 400

    def __init__(self, i2c):
        super().__init__(i2c)
        self._calibrate_imu()

        self._accel_offset = None
        self._gyro_offset = None

    def _verify_sensor_device(self):
        while True:
            try:
                # Create BNO08X IMU object
                self._imu = BNO08X_I2C(self._i2c)

                self._imu.enable_feature(BNO_REPORT_ACCELEROMETER)
                self._imu.enable_feature(BNO_REPORT_GYROSCOPE)
                self._imu.enable_feature(BNO_REPORT_MAGNETOMETER)
                self._imu.enable_feature(BNO_REPORT_ROTATION_VECTOR)
                self._imu.enable_feature(BNO_REPORT_LINEAR_ACCELERATION)

                # Verify sensor is responding by reading a value
                _ = self._imu.acceleration
                _ = self._imu.gyro
                _ = self._imu.magnetic
                _ = self._imu.quaternion
                _ = self._imu.linear_acceleration
                print("BNO08X IMU initialized successfully")
                break
            except:
                print(f"BNO08X IMU sensor initialization failed. Retrying in {IMUSensorController.SENSOR_VERIFY_ATTEMPT_DELAY} seconds...")
                time.sleep(IMUSensorController.SENSOR_VERIFY_ATTEMPT_DELAY)
        
        self._verification_thread = None

    def get_sensor_data(self) -> object:
        """
        Get the IMU sensor data.
        """
        if self._verification_thread:
            print("IMU sensor verification in progress. Returning None for sensor data.")
            return None

        try:
            acceleration = self._imu.acceleration
            gyro = self._imu.gyro
            magnetometer = self._imu.magnetic
            rot_vector = self._quaternion_to_euler(self._imu.quaternion)
            gravity = self._imu.gravity
            linear_acceleration = self._imu.linear_acceleration
            return {
                "acceleration": {"x": acceleration[0], "y": acceleration[1], "z": acceleration[2]},
                "gyro": {"x": gyro[0], "y": gyro[1], "z": gyro[2]},
                "magnetometer": {"x": magnetometer[0], "y": magnetometer[1], "z": magnetometer[2]},
                "vector_orientation": {"r": rot_vector[0], "p": rot_vector[1], "y": rot_vector[2]},
                "linear_acceleration": {"x": linear_acceleration[0], "y": linear_acceleration[1], "z": linear_acceleration[2]},
                "gravity": {"x": gravity[0], "y": gravity[1], "z": gravity[2]}
            }

        except Exception as e:
            print(f"Error reading IMU sensor data: {e}")
            self._attempt_troubleshoot_device()
            return None
        

    def _calibrate_imu(self):
        # Number of samples used to compute calibration offsets
        SAMPLES = IMUSensorController.CALIBRATION_SAMPLES

        # Accumulators for accelerometer and gyroscope readings
        ax = ay = az = 0.0
        gx = gy = gz = 0.0

        # Collect samples while the sensor is stationary
        for _ in range(SAMPLES):
            a = self._imu.acceleration  # Acceleration in m/s²
            g = self._imu.gyro          # Angular velocity in rad/s

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
        

    def _quaternion_to_euler(self, quaternion: tuple) -> tuple:
        w, x, y, z = quaternion
        # Roll (X-axis rotation)
        roll = math.atan2(2*(w*x + y*z), 1 - 2*(x*x + y*y))
        # Pitch (Y-axis rotation)
        pitch = math.asin(2*(w*y - z*x))
        # Yaw (Z-axis rotation)
        yaw = math.atan2(2*(w*z + x*y), 1 - 2*(y*y + z*z))
        # Convert radians to degrees
        return math.degrees(roll), math.degrees(pitch), math.degrees(yaw)