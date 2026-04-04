import RPi.GPIO as GPIO
import time
import threading

__all__ = ["ServoController"]

class ServoController:
    SERVO_UPDATE_INTERVAL = 0.05

    def __init__(self, pin: int):
        self._servo_pin = pin
        self._target_angle = 0.0

        # Setup GPIO
        GPIO.setmode(GPIO.BCM)           # Use BCM numbering
        GPIO.setup(self._servo_pin, GPIO.OUT)

        # Setup PWM at 50Hz (standard for servo)
        self._pwm = GPIO.PWM(self._servo_pin, 50)
        self._pwm.start(0)  # start with 0 duty cycle

        # Thread
        self._update_thread = threading.Thread(target=self._main)
        self._update_thread.daemon = True
        self._update_thread.start()

    def _main(self):
        while True:
            time.sleep(ServoController.SERVO_UPDATE_INTERVAL)

    def set_servo_angle(self, angle: float, delay_for_completion: bool = True):
        """Set servo angle. Supports 0..180 absolute, and negative offsets around midpoint."""
        original_angle = angle

        if angle < 0:
            angle = 90 + angle

        if angle < 0 or angle > 180:
            print(f"⚠️  Attempted to set servo angle out of bounds: {original_angle}. Clamping to valid range.")

        angle = max(0, min(180, angle))          # clamp angle
        duty = 2 + (angle / 18)                  # convert angle to duty cycle
        self._pwm.ChangeDutyCycle(duty)
        self._target_angle = angle    
        if delay_for_completion:
            time.sleep(0.3)                           # give servo time to move
        self._pwm.ChangeDutyCycle(0)             # stop sending signal

    def get_servo_angle(self) -> float:
        """Return the last commanded angle (cannot read actual angle)"""
        return self._target_angle

    def turn_off_servo(self):
        self._pwm.ChangeDutyCycle(0)
        self._pwm.stop()