from rocket_gcs_communication import RocketCommunication
from rocket_controller import RocketController

def main():
    # Initialize Rocket Controller
    rocket_controller = RocketController()

    # Initialize Rocket GCS Communication
    rocket_communication = RocketCommunication(rocket_controller)

if __name__ == "__main__":
    main()