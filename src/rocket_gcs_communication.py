import adafruit_rfm9x
import board
import busio
import digitalio

import time

from rocket_controller import RocketController

class RocketCommunication:
    def __init__(self, rocket_controller: RocketController, radio_freq_mhz: float = 915.0):
        # Initialize RocketCommunication with RocketController and radio frequency
        self._rocket_controller = rocket_controller
        self._radio_freq_mhz = radio_freq_mhz
        self._rfm9x = None

        # Verify & Initialize RFM9x device connection
        self._verify_rfm9x_device()        
        
    def _verify_rfm9x_device(self):
        """
        Verify the RFM9x device is connected and wired connection.
        """
        while True:
            try:
                # Define pins connected to the RFM9x
                CS = digitalio.DigitalInOut(board.CE1)
                RESET = digitalio.DigitalInOut(board.D25)

                # Initialize SPI bus
                spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)

                # Initialize RFM9x
                rfm9x = adafruit_rfm9x.RFM9x(spi, CS, RESET, self._radio_freq_mhz)
                self._rfm9x = rfm9x
                print("✅ RFM9x found and initialized.")
            except:
                print("❌ RFM9x not found, retrying...")

            # Delay
            time.sleep(0.2)

    def send_data(self, data: object):
        """
        Send data via RFM9x.
        """
        # 
