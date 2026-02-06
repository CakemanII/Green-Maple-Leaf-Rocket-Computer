from rocket_controller import RocketController

import time
import threading

class RocketSensorData:
    def __init__(self, rocketController: RocketController):
        self._rocket_controller = rocketController

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
    
    def _update_sensor_data(self):
        """
        Update the sensor data by retrieving the latest data from the rocket controller.
        """
        data = self._rocket_controller.get_gps_sensor_data()
        self._gps_data = (time.time(), data)
        data = self._rocket_controller.get_dps_sensor_data()
        self._dps_data = (time.time(), data)
        data = self._rocket_controller.get_imu_sensor_data()
        self._imu_data = (time.time(), data)


    def _main(self, update_interval: float):
        """
        Start a continuous loop to update the sensor data at a specified interval.
        """
        while True:
            self.update_sensor_data()
            time.sleep(update_interval)


    def start_updating(self):
        """
        Start the continuous sensor data update in a separate thread.
        """
        update_thread = threading.Thread(target=self._main, args=(1.0,))
        update_thread.daemon = True
        update_thread.start()