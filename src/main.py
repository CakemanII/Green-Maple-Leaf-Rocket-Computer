from datetime import datetime

import rocket_controller
from rocket_gcs_communication import RocketCommunication
from rocket_controller import RocketController
from commands_list import RocketCommand
from rocket_sensor_data import RocketSensorData

import time

class RocketComputer:
    def __init__(self):
        # Initialize Rocket Controller
        self._rocket_controller = RocketController()

        # Initialize Rocket GCS Communication and start communication
        # self._rocket_communication = RocketCommunication(self._rocket_controller)
        
        # Initialize sensor data management
        self._rocket_sensor_data = RocketSensorData(self._rocket_controller)
        self._rocket_sensor_data.start()

        # Add listeners for commands
        # self._add_command_listeners()
        
        # Start communication
        # self._rocket_communication.start_communication()

        # Start main control loop
        self._main_test()

    def _main_test(self):
        while True:
            time.sleep(0.25)
            print("Sensor Data: IMU, GPS, DPS | " + str(datetime.now()))
            gps_data = self._rocket_sensor_data.get_gps_data()
            imu_data = self._rocket_sensor_data.get_imu_data()
            dps_data = self._rocket_sensor_data.get_dps_data()
            print(f"GPS: {gps_data}")
            print(f"IMU: {imu_data}")
            print(f"DPS: {dps_data}")
            print("--------------------------------------------------" + "\n"*20)

            dps_is_valid = dps_data is not None
            imu_is_valid = imu_data is not None
            gps_is_valid = gps_data is not None
            self._rocket_controller._lcd.set_live_scrolling_text(f"D: {dps_is_valid} I: {imu_is_valid} G: {gps_is_valid}", 0)


    def _add_command_listeners(self):
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

    def _main(self):
        """
        Main control loop for the rocket computer.
        """
        while True:
            print("🚀 Rocket Computer Main Loop Iteration")
            # Check if we should deploy the parachute
            self._detect_deploy_parachute()
            time.sleep(0.05)

    def _send_continuous_telemetry_data(self):
        while True:
            # Get sensor data
            imu_data = self._rocket_sensor_data.get_imu_data()
            gps_data = self._rocket_sensor_data.get_gps_data()

            # Send data to ground station
            self._rocket_communication.send_data({
                "imu": imu_data,
                "gps": gps_data,
            })

            time.sleep(0.1)

    def _detect_deploy_parachute(self):
        """
        Determine when to deploy the parachute.
        """
        # Ensure parachute trigger has not been deployed yet.
        if not self._rocket_controller.is_co2_breach_triggered():
            return

        # Acceleration
        if not self._rocket_sensor_data.get_imu_data()['acceleration'] < 0:
            return
        
        # Velocity
        if not abs(self._rocket_sensor_data.get_imu_data()['velocity']) < 0.1:
            return

        # Magnometer
        # ...

        # At least 3 after launch 
        # ...

        # At least 50m high
        if not self._rocket_sensor_data.get_gps_data()['altitude'] > 50:
            return

        # All conditions met, breach co2 & deploy parachute
        self._rocket_controller.breach_co2_canister()

if __name__ == "__main__":
    RocketComputer()