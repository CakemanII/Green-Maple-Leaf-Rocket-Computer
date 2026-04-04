import threading

class SensorController:
    SENSOR_VERIFY_ATTEMPT_DELAY = 0.1
    
    def __init__(self, i2c=None):
        self._sensor = None
        self._verification_thread = None
        self._i2c = i2c

        # Verify the sensor device is connected and responsive
        self._verify_sensor_device()

    def _verify_sensor_device(self):
        """
        Verify the sensor device is connected and responsive.
        """
        raise NotImplementedError("This method should be implemented by subclasses.")

    def _get_sensor_data(self) -> object:
        """
        Get the sensor data.
        """
        raise NotImplementedError("This method should be implemented by subclasses.")
    
    def _attempt_troubleshoot_device(self):
        if self._verification_thread is None:
            self._verification_thread = threading.Thread(target=self._verify_sensor_device)
            self._verification_thread.start()