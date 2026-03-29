from rocket_controller import RocketController

import time
import threading

class RocketSensorData:
    def __init__(self, rocketController: RocketController, interval: float = 0.15):
        self._rocket_controller = rocketController
        self._update_interval = interval

        # Initialize sensor data
        self._gps_data = None
        self._dps_data = None
        self._imu_data = None
        self._raspi_cam_data = None
        self._raspi_computer_data = None

    # region Getters
    def get_gps_data(self) -> object: return self._gps_data
    def get_dps_data(self) -> object: return self._dps_data
    def get_imu_data(self) -> object: return self._imu_data
    # endregion

    def _update_dps(self):
        """
        Start a continuous loop to update the sensor data at a specified interval.
        """
        while True:
            self._dps_data = (time.time(), self._rocket_controller.get_dps_sensor_data())
            time.sleep(self._update_interval)

    def _update_gps(self):
        """
        Start a continuous loop to update the GPS sensor data at a specified interval.
        """
        while True:
            self._gps_data = (time.time(), self._rocket_controller.get_gps_sensor_data())
            time.sleep(self._update_interval)

    def _update_imu(self):
        """
        Start a continuous loop to update the IMU sensor data at a specified interval.
        """
        while True:
            self._imu_data = (time.time(), self._rocket_controller.get_imu_sensor_data())
            time.sleep(self._update_interval)

    def _update_raspi_computer(self):
        """
        Start a continuous loop to update the Raspberry Pi computer stats at a specified interval.
        """
        while True:
            self._raspi_computer_data = (time.time(), self._rocket_controller.get_raspi_stats())
            time.sleep(self._update_interval)

    def start(self):
        """
        Start the continuous sensor data update in a separate thread.
        """
        update_thread = threading.Thread(target=self._update_dps)
        update_thread.daemon = True
        update_thread.start()

        update_thread = threading.Thread(target=self._update_gps)
        update_thread.daemon = True
        update_thread.start()

        update_thread = threading.Thread(target=self._update_imu)
        update_thread.daemon = True
        update_thread.start()