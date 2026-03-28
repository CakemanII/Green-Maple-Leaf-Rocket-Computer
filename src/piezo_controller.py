import RPi.GPIO as GPIO
import time
import threading

class PiezoController:
    ITERATION_DELAY: float = 0.1
    PIEZO_PIN = 22

    def __init__(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(PiezoController.PIEZO_PIN, GPIO.OUT)
        self._pwm = GPIO.PWM(PiezoController.PIEZO_PIN, 100)  # 1 kHz frequency
        self._pwm.start(0)  # Start with 0% duty cycle (off)

        self._frequency = None
        self._volume = None

        # Start the main loop in a separate thread
        self._main_thread = threading.Thread(target=self._main)
        self._main_thread.daemon = True
        self._main_thread.start()

    def _main(self):
        while True:
            if self._frequency is not None:
                self._pwm.ChangeFrequency(self._frequency)
            else:
                self._pwm.ChangeDutyCycle(0)  # Turn off the buzzer if frequency is not set

            if self._volume is not None:
                self._pwm.ChangeDutyCycle(self._volume / 2.0)  # Set volume (duty cycle)
            else:
                self._pwm.ChangeDutyCycle(0)  # Turn off the buzzer if volume is not set

            time.sleep(self.ITERATION_DELAY)

    def set_buzzer(self, frequency: float, volume: float):
        self._frequency = min(20000, max(20, frequency))  # Limit frequency to human hearing range
        self._volume = min(100, max(0, volume)) / 2.0

    def stop_buzzer(self):
        self._frequency = None
        self._volume = None
        self._pwm.ChangeDutyCycle(0)  # Turn off the buzzer
