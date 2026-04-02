import time
from datetime import datetime

class CameraController():
    CAMERA_CHECK_INTERVAL = 0.05

    def __init__(self):
        self._session = None
        self._recording_path = None

        # Verify the camera
        self._verify_camera()

    def _main(self):
        while True:
            # Check if the camera is verified
            time.sleep(CameraController.CAMERA_CHECK_INTERVAL)
            

    def _verify_camera(self):
        # Verify the camera is working
        pass

    def generate_recording_path(self):
        current_time: str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self._recording_path = f"recordings/recording_{current_time}.mp4"

    def set_camera_record_session(self, session: str):
        # Set the camera recording session.
        self._session = session

    def start_camera_recording(self):
        # Start the camera recording.
        self.generate_recording_path()
        pass

    def stop_camera_recording(self):
        # Stop the camera recording.
        pass

    def get_camera_recording_status(self) -> bool:
        # Get the camera recording status.
        pass

    