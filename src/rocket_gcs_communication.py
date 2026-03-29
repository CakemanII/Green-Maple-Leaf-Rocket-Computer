from typing import TypedDict

import adafruit_rfm9x
import board
import busio
import digitalio
import threading

import time
import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding

from rocket_controller import RocketController
from commands_list import RocketCommand

class RadioDataObject(TypedDict):
    l: str # input telemetry_id / label
    s: float # timestamp this was sent
    d: object # data (can be any JSON-serializable object)

class RocketCommunication:
    SENSOR_VERIFY_ATTEMPT_DELAY = 0.2

    def __init__(self, rocket_controller: RocketController, radio_freq_mhz: float = 915.0, aes_key: bytes = None):
        # Initialize RocketCommunication with RocketController and radio frequency
        self._rocket_controller = rocket_controller
        self._radio_freq_mhz = radio_freq_mhz
        self._rfm9x = None
        self._listeners: dict[str, list[callable]] = {}

        # AES encryption key (32 bytes for AES-256)
        if aes_key is None:
            # Generate a random 32-byte key if none provided
            self._aes_key = os.urandom(32)
            print(f"⚠️  Generated new AES key: {self._aes_key.hex()}")
            print("    Save this key for the ground station!")
        else:
            if len(aes_key) not in [16, 24, 32]:
                raise ValueError("AES key must be 16, 24, or 32 bytes")
            self._aes_key = aes_key
            print(f"✅ Using provided AES-{len(aes_key)*8} key")

        # Verify RFM9x device is connected and wired connection
        self._verify_rfm9x_device()

    # region Communication Management
    def start_communication(self):
        """
        Start the communication thread.
        """
        comm_thread = threading.Thread(target=self._main, daemon=True)
        comm_thread.start()
        
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
                break
            except:
                print("❌ RFM9x not found, retrying...")
                time.sleep(RocketCommunication.SENSOR_VERIFY_ATTEMPT_DELAY)
    # endregion

    def _main(self):
        """
        Main loop to check for incoming data.
        """
        self._verify_rfm9x_device()

        while True:
            # Delay
            time.sleep(0.1)
            
            # Check for incoming packet
            try:
                packet = self._rfm9x.receive(timeout=0.5)
            except:
                print("❌ RFM9x connection lost, reinitializing...")
                self._verify_rfm9x_device()
                continue
            
            # Don't continue if no packet received
            if packet is None:
                continue
            
            # Process received packet
            self._on_receive_data(packet)

    # region AES Encryption/Decryption
    def _encrypt_aes(self, data: bytes) -> bytes:
        """
        Encrypt data using AES-256-CBC.
        Returns: IV (16 bytes) + encrypted data
        """
        # Generate random initialization vector
        iv = os.urandom(16)
        
        # Create cipher
        cipher = Cipher(
            algorithms.AES(self._aes_key),
            modes.CBC(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        
        # Pad data to AES block size (128 bits / 16 bytes)
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(data) + padder.finalize()
        
        # Encrypt
        encrypted = encryptor.update(padded_data) + encryptor.finalize()
        
        # Return IV + encrypted data (IV needed for decryption)
        return iv + encrypted

    def _decrypt_aes(self, encrypted_data: bytes) -> bytes:
        """
        Decrypt AES-256-CBC encrypted data.
        Expects: IV (16 bytes) + encrypted data
        """
        # Extract IV and ciphertext
        iv = encrypted_data[:16]
        ciphertext = encrypted_data[16:]
        
        # Create cipher
        cipher = Cipher(
            algorithms.AES(self._aes_key),
            modes.CBC(iv),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()
        
        # Decrypt
        padded_data = decryptor.update(ciphertext) + decryptor.finalize()
        
        # Unpad
        unpadder = padding.PKCS7(128).unpadder()
        data = unpadder.update(padded_data) + unpadder.finalize()
        
        return data
    # endregion

    def send_data(self, label: str, data: object):
        """
        Send data via RFM9x.
        """
        # Get current seconds
        time_seconds = time.time()

        # Create object
        data_packet: RadioDataObject = {
            "l": label,
            "s": time_seconds,
            "d": data
        }

        # Convert to bytes
        byte_data = str(data_packet).encode("utf-8")
        
        # Encrypt with AES
        encrypted_data = self._encrypt_aes(byte_data)

        # Send via RFM9x
        self._rfm9x.send(encrypted_data)

    def _on_receive_data(self, packet) -> None:
        """
        Receive data via RFM9x.
        Send to appropriate listeners.
        """
        try:
            # Decrypt packet
            decrypted_bytes = self._decrypt_aes(packet)
            
            # Convert bytes back to object
            data_str = decrypted_bytes.decode("utf-8")
            data_obj = eval(data_str)  # Caution: eval can be dangerous

            # Notify listeners
            label = data_obj.get("l", "")
            if label in self._listeners:
                for callback in self._listeners[label]:
                    callback(data_obj)
            
            return data_obj
        except Exception as e:
            print(f"❌ Error decrypting/processing received data: {e}")

    def add_listener(self, label: str, callback: callable) -> None:
        """
        Add a listener for incoming data with a specific label.
        """
        if label not in self._listeners:
            self._listeners[label] = []
        self._listeners[label].append(callback)