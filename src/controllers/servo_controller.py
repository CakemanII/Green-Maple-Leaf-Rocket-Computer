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

    def set_servo_angle(self, angle: float, forward: bool = True, threaded: bool = True):
        """
        Set servo angle with direction.
        Args:
            angle: 0-360 degrees
            forward: True for forward direction, False for backward
            threaded: Run in separate thread
        """
        if threaded:
            threading.Thread(target=self._do_move_servo, args=(angle, forward)).start()
        else:
            self._do_move_servo(angle, forward)

    def _do_move_servo(self, angle: float, forward: bool):
        """
        Set servo angle with direction.
        Accepts 0-360 degrees and maps to servo's 0-180 range based on direction.
        """
        original_angle = angle
        
        # Clamp angle to 0-360 range
        if angle < 0 or angle > 360:
            print(f"⚠️  Attempted to set servo angle out of bounds: {original_angle}. Clamping to valid range.")
        
        angle = max(0, min(360, angle))
        
        # Map 0-360 to 0-180 range
        servo_angle = (angle / 360) * 180
        
        # Apply direction - if backward, reverse the angle
        if not forward:
            servo_angle = 180 - servo_angle
        
        # Convert angle to duty cycle
        duty = 2 + (servo_angle / 18)
        self._pwm.ChangeDutyCycle(duty)
        self._target_angle = servo_angle
        time.sleep(0.3)                           # give servo time to move
        self._pwm.ChangeDutyCycle(0)             # stop sending signal

    def get_servo_angle(self) -> float:
        """Return the last commanded angle (cannot read actual angle)"""
        return self._target_angle

    def rest_servo(self):
        self._pwm.ChangeDutyCycle(0)
        self._pwm.stop()