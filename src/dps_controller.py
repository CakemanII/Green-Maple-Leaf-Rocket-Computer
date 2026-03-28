import adafruit_dps310
import time
import threading
from sensor_controller import SensorController

class DPSSensorController(SensorController):
    def __init__(self, i2c):
        super().__init__(i2c)

    def _verify_sensor_device(self):
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
                print(f"DPS310 sensor initialization failed. Retrying in {DPSSensorController.SENSOR_VERIFY_ATTEMPT_DELAY} seconds...")
                time.sleep(DPSSensorController.SENSOR_VERIFY_ATTEMPT_DELAY)
        
        self._verification_thread = None

    def get_sensor_data(self) -> object:
        """
        Get the DPS sensor data.
        """
        if self._verification_thread:
            print("DPS sensor verification in progress. Returning None for sensor data.")
            return None

        try:
            pressure = self._dps.pressure
            altitude = self._dps.altitude
            temperature = self._dps.temperature
            print("Retreved data"*25)
            return {
                "pressure": pressure,
                "altitude": altitude,
                "temperature": temperature
            }

        except Exception as e:
            print(f"Error reading DPS sensor data: {e}")
            self._attempt_troubleshoot_device()
            return None