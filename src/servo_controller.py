import GPIO
import threading
import time
import pigpio

class ServoController():
    SERVO_UPDATE_INTERVAL = 0.05

    def __init__(self, pin: int):
        # Set Variables
        self._servo_pin = pin
        self._target_angle = 0.0

        # Setup Servo
        self._pi = pigpio.pi()


    def set_servo_angle(self, angle: float):
        pulsewidth = 500 + (angle * 2000 / 180)  # 500–2500 µs
        self._pi.set_servo_pulsewidth(self._servo_pin, pulsewidth)


    def get_servo_angle(self) -> float:
        pulsewidth = self._pi.get_servo_pulsewidth(self._servo_pin)
    
        if pulsewidth == 0:
            return None  # servo off / no signal
        
        angle = (pulsewidth - 500) * 180 / 2000
        return angle