import RPi.GPIO as GPIO

class FansController:
    def __init__(self, gpio: int):
        self.gpio = gpio
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.gpio, GPIO.OUT)

        # Initialize PWM at 25kHz (typical for fans)
        self.pwm = GPIO.PWM(self.gpio, 25000)
        self.pwm.start(0)  # Start with fan off

    def set_fan_speed(self, speed: int):
        # Clamp speed between 0 and 100
        speed = max(0, min(100, speed))

        # Change duty cycle to control speed
        self.pwm.ChangeDutyCycle(speed)

    def cleanup(self):
        self.pwm.stop()
        GPIO.cleanup(self.gpio)