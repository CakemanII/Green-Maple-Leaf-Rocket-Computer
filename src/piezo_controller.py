import RPi.GPIO as GPIO
import time
import threading

MusicalTone = list[tuple[float, float, float]]  # List of (frequency, volume, duration) pairs
    
class PresetMusicalTones:
    SUCCESS_TONE: MusicalTone = [
        (523, 80, 0.10),   # C5
        (659, 80, 0.10),   # E5
        (784, 80, 0.10),   # G5
        (1047, 90, 0.15),  # C6
    ]

    FAILURE_TONE: MusicalTone = [
        (494, 80, 0.10),  # B4
        (0,   0,  0.03),  # silence
        (466, 80, 0.10),  # Bb4
        (0,   0,  0.03),  # silence
        (440, 80, 0.10),  # A4
        (0,   0,  0.03),  # silence
        (330, 90, 0.15),  # E4 - low thud
    ]

    VERIFICATION_TONE: MusicalTone = [
        # Work
        (392.00, 0.8, 0.2), (466.16, 0.8, 0.2),

        # it
        (392.00, 0.8, 0.2), (466.16, 0.8, 0.2),

        # hard-
        (466.16, 0.8, 0.2), (523.25, 0.8, 0.2),

        # er
        (392.00, 0.8, 0.2), (466.16, 0.8, 0.2),

        # make
        (349.23, 0.8, 0.2), (392.00, 0.8, 0.2),

        # it
        (392.00, 0.8, 0.2), (466.16, 0.8, 0.2),

        # bet-
        (466.16, 0.8, 0.2), (523.25, 0.8, 0.2),

        # ter
        (392.00, 0.8, 0.2), (466.16, 0.8, 0.2),
    ]

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
        self.is_playing_tone = False

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
            
            if self._frequency is not None and self._volume is not None:
                self.is_playing_tone = True
            else:
                self.is_playing_tone = False

            time.sleep(self.ITERATION_DELAY)

    def set_buzzer(self, frequency: float, volume: float):
        self._frequency = min(20000, max(20, frequency))  # Limit frequency to human hearing range
        self._volume = min(100, max(0, volume)) / 2.0

    def stop_buzzer(self):
        self._frequency = None
        self._volume = None

    def play_tone(self, tone: MusicalTone, threaded: bool = True):
        if threaded:
            threading.Thread(target=self._do_play_tone, args=(tone,), daemon=True).start()
        else:
            self._do_play_tone(tone)

    def _do_play_tone(self, tone: MusicalTone):
        for frequency, volume, duration in tone:
            current_time = time.time()
            if frequency == 0 or volume == 0:
                self.stop_buzzer()
            else:
                self.set_buzzer(frequency, volume)
            time.sleep(max(0, duration - (time.time() - current_time)))  # Adjust sleep time to account for processing delay
        self.stop_buzzer()
