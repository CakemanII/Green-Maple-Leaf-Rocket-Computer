import rocket_controller
from rocket_gcs_communication import RocketCommunication
from rocket_controller import RocketController
from commands_list import RocketCommand

class RocketComputer:
    def __init__(self):
        # Initialize Rocket Controller
        self._rocket_controller = RocketController()

        # Initialize Rocket GCS Communication and start communication
        self._rocket_communication = RocketCommunication(self._rocket_controller)
        
        # Add listeners for commands
        self._add_listeners()
        
        # Start communication
        self._rocket_communication.start_communication()


    def _add_listeners(self):
        """
        Add listeners for commands.
        """
        # Toggle Stop receiving Commands
        self._rocket_communication.add_listener(
            RocketCommand.STOP_RECEIVING, 
            None
        )

        # Toggle A Specific Sensor's Data Transmission
        self._rocket_communication.add_listener(
            RocketCommand.TOGGLE_SENSOR_DATA_TRANSMISSION, 
            None
        )

        # System Shutdown
        self._rocket_communication.add_listener(
            RocketCommand.SHUTDOWN_SYSTEM, 
            None
        )

        # Toggle Automatic Parachute Deployment
        self._rocket_communication.add_listener(
            RocketCommand.TOGGLE_AUTOMATIC_DEPLOYMENT, 
            None
        )

        # Manual Breach CO2 Canister
        self._rocket_communication.add_listener(
            RocketCommand.MANUAL_PARACHUTE_DEPLOYMENT, 
            self._rocket_controller.breach_co2_canister
        )

        # Toggle Camera
        self._rocket_communication.add_listener(
            RocketCommand.TOGGLE_ONBOARD_RASPI_CAM, 
            self._rocket_controller.toggle_rocket_camera_state
        )


    def detect_deploy_parachute(self):
        """
        Determine when to deploy the parachute.
        """
        


if __name__ == "__main__":
    RocketComputer()