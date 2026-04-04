import serial
from controllers.sensor_controller import SensorController

import pynmea2

class GPSSensorController(SensorController):
    PORT = "/dev/ttyAMA0"
    BAUD = 9600

    def _verify_sensor_device(self):
        # Open serial connection to GPS
        self._ser = serial.Serial(GPSSensorController.PORT, GPSSensorController.BAUD, timeout=1)

    def get_sensor_data(self) -> object:
        """
        Get the GPS sensor data.
        """
        try:
            # Read one NMEA sentence from the GPS
            line = self._ser.readline().decode("ascii", errors="replace")

            # Process GPGGA sentences (contain fix data)
            if line.startswith("$GPGGA"):
                msg = pynmea2.parse(line)
                # print("entire:" + str(msg))
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
        except Exception as e:
            print(f"Error reading GPS sensor data: {e}")
            self._attempt_troubleshoot_device()
            return None