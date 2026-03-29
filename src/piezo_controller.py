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
        # -- Bar 1 --
        (185, 85, 0.12),   # Bb2  (A string fret 7 - half step down)
        (0,   0,  0.03),
        (220, 85, 0.12),   # A2   (A string fret 10 - half step down)
        (0,   0,  0.03),
        (185, 85, 0.12),   # Bb2
        (0,   0,  0.03),
        (220, 85, 0.12),   # A2
        (0,   0,  0.03),
        (233, 85, 0.12),   # Bb2  (A string fret 10)
        (0,   0,  0.03),
        (185, 85, 0.12),   # Bb2
        (0,   0,  0.03),
        (220, 85, 0.12),   # A2
        (0,   0,  0.03),
        (185, 90, 0.20),   # Bb2  held

        # -- Bar 2 --
        (156, 85, 0.12),   # Eb2  (low E string fret 10)
        (0,   0,  0.03),
        (156, 85, 0.12),   # Eb2
        (0,   0,  0.03),
        (175, 85, 0.12),   # F2   (low E string fret 10)
        (0,   0,  0.03),
        (175, 85, 0.12),   # F2
        (0,   0,  0.03),
        (156, 85, 0.12),   # Eb2
        (0,   0,  0.03),
        (175, 85, 0.12),   # F2
        (0,   0,  0.03),
        (147, 90, 0.30),   # D2   (low E string fret 9) - resolve

        # -- Bar 3 (repeat bar 1) --
        (185, 85, 0.12),   # Bb2
        (0,   0,  0.03),
        (220, 85, 0.12),   # A2
        (0,   0,  0.03),
        (185, 85, 0.12),   # Bb2
        (0,   0,  0.03),
        (220, 85, 0.12),   # A2
        (0,   0,  0.03),
        (233, 85, 0.12),   # Bb2
        (0,   0,  0.03),
        (185, 85, 0.12),   # Bb2
        (0,   0,  0.03),
        (220, 85, 0.12),   # A2
        (0,   0,  0.03),

        # -- Bar 4 (ending) --
        (156, 85, 0.12),   # Eb2
        (0,   0,  0.03),
        (156, 85, 0.12),   # Eb2
        (0,   0,  0.03),
        (139, 90, 0.40),   # Db2  - low held ending note
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

    def play_tone(self, tone: MusicalTone, threaded: bool = True):
        if threaded:
            threading.Thread(target=self._do_play_tone, args=(tone,), daemon=True).start()
        else:
            self._do_play_tone(tone)

    def _do_play_tone(self, tone: MusicalTone):
        for frequency, volume, duration in tone:
            if frequency == 0:
                self.stop_buzzer()
            else:
                self.set_buzzer(frequency, volume)
            time.sleep(duration)
        self.stop_buzzer()
