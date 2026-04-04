import RPi.GPIO as GPIO
import time
import threading

__all__ = ["ServoController"]

class ServoController:
    SERVO_UPDATE_INTERVAL = 0.05

    def __init__(self, pin: int, continuous_rotation: bool = True):
        self._servo_pin = pin
        self._target_angle = 0.0
        self._continuous_rotation = continuous_rotation

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

    def set_servo_angle(self, angle: float, threaded: bool = True):
        """For standard servos only (0-180 degrees)."""
        if threaded:
            threading.Thread(target=self._do_move_servo, args=(angle,)).start()
        else:
            self._do_move_servo(angle)

    def set_continuous_rotation(self, speed: float, forward: bool = True, threaded: bool = True):
        """
        For continuous rotation servos.
        Args:
            speed: 0-360 (speed of rotation)
            forward: True for forward, False for backward
            threaded: Run in separate thread
        """
        if threaded:
            threading.Thread(target=self._do_continuous_rotation, args=(speed, forward)).start()
        else:
            self._do_continuous_rotation(speed, forward)

    def _do_move_servo(self, angle: float):
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
        time.sleep(0.3)                           # give servo time to move
        self._pwm.ChangeDutyCycle(0)             # stop sending signal

    def _do_continuous_rotation(self, speed: float, forward: bool):
        """
        Control continuous rotation servo.
        For continuous servos: 0° = full reverse, 90° = stop, 180° = full forward
        """
        # Clamp speed to 0-360 range
        speed = max(0, min(360, speed))
        
        # Map 0-360 speed to 0-90 range (0 = stop, 90 = full speed)
        # This gives finer control over the speed
        speed_mapped = (speed / 360) * 90
        
        # Calculate servo angle based on direction
        # Forward: 90° (stop) to 180° (full forward)
        # Backward: 90° (stop) to 0° (full backward)
        if forward:
            servo_angle = 90 + speed_mapped  # 90 to 180
        else:
            servo_angle = 90 - speed_mapped  # 90 to 0
        
        # Convert angle to duty cycle
        duty = 2 + (servo_angle / 18)
        self._pwm.ChangeDutyCycle(duty)
        self._target_angle = servo_angle
        
        # For continuous rotation, keep signal active (don't stop)
        # User must call stop() to stop rotation

    def stop(self):
        """Stop continuous rotation servo."""
        # Set to neutral position (90° = stop for continuous servos)
        duty = 2 + (90 / 18)
        self._pwm.ChangeDutyCycle(duty)
        self._target_angle = 90

    def get_servo_angle(self) -> float:
        """Return the last commanded angle (cannot read actual angle)"""
        return self._target_angle

    def rest_servo(self):
        self._pwm.ChangeDutyCycle(0)
        self._pwm.stop()