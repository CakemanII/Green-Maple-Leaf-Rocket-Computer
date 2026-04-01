from datetime import datetime

from rocket_controller import RocketController
from rocket_communication import RocketCommunication
from telemetry_data_transfer_types_retrieval import TelemetryDataTransferTypes
from rocket_controller import RocketController
from commands_list import RocketCommand
from rocket_sensor_data import RocketSensorData
import RPi.GPIO as GPIO

from data_compression import TelemetryObject

import time

class RocketComputer:
    def __init__(self):
        # Initialize the telemetry_data_transfer_types
        self._telemetry_data_transfer_types = TelemetryDataTransferTypes()

        # Initialize Rocket GCS Communication
        self._rocket_communication = RocketCommunication(telemetry_data_transfer_types=self._telemetry_data_transfer_types)

        # Initialize Rocket Controller
        self._rocket_controller = RocketController()
        
        # Initialize sensor data management
        self._rocket_sensor_data = RocketSensorData(self._rocket_controller)
        self._rocket_sensor_data.start()

        self._rocket_controller._lcd.clear()
        self._rocket_controller._lcd.print_line("Verifying RFM9X", 0)

        

        # Add listeners for commands
        self._add_command_listeners()
        
        # Start communication
        self._rocket_communication.set_active()

        # Start main control loop
        self._main_test()

    def _main_test(self):
        while True:
            # Collect telemetry as list of TelemetryObject instances
            telemetry_objects: list[TelemetryObject] = []
            current_timestamp = time.time()

            # IMU
            imu_data = self._rocket_sensor_data.get_imu_data()
            if imu_data is not None and imu_data[1] is not None:
                imu_values = imu_data[1]
                telemetry_objects.append({"label": "imu.acc", "timestamp": current_timestamp, "data": imu_values["acceleration"]})
                telemetry_objects.append({"label": "imu.anv", "timestamp": current_timestamp, "data": imu_values["gyro"]})
                telemetry_objects.append({"label": "imu.mgn", "timestamp": current_timestamp, "data": imu_values["magnetometer"]})
                telemetry_objects.append({"label": "imu.grv", "timestamp": current_timestamp, "data": imu_values["gravity"]})
                telemetry_objects.append({"label": "imu.ori", "timestamp": current_timestamp, "data": imu_values["vector_orientation"]})
                telemetry_objects.append({"label": "imu.lac", "timestamp": current_timestamp, "data": imu_values["linear_acceleration"]})

                # Send entire batch as single compressed transmission
                if telemetry_objects:
                    self._rocket_communication.send_data(("d1", telemetry_objects))
                telemetry_objects: list[TelemetryObject] = []


            # LCD Status Display
            dps_data = None
            gps_data = None
            imu_is_valid = "OP" if imu_data is not None and imu_data[1] is not None else "ERR"
            dps_is_valid = "OP" if dps_data is not None and dps_data[1] is not None else "ERR"
            gps_is_valid = "OP" if gps_data is not None and gps_data[1] is not None else "ERR"
            piezo_is_valid = "ON" if self._rocket_controller._piezo.is_playing_tone else "OFF"
            self._rocket_controller._lcd.set_live_scrolling_text(f"STATE: READY  CON: 50ms  RTMP: 25°C", 0)
            self._rocket_controller._lcd.set_live_scrolling_text(
                f"DPS: {dps_is_valid}  IMU: {imu_is_valid}  GPS: {gps_is_valid}  CAM: OP  FAN: 0%  PIEZO: {piezo_is_valid} ", 1, delay=0.22)

            # Prevent flooding worker queues (LCD + radio) and reduce bus contention.
            time.sleep(0.1)


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
    try:
        RocketComputer()
    finally:
        print("Cleaning up GPIO...")
        GPIO.cleanup()