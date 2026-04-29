from datetime import datetime
from threading import Thread

from rocket_controller import RocketController
from rocket_communication import RocketCommunication
from communication.telemetry_data_transfer_types_retrieval import TelemetryDataTransferTypes
from communication.commands_list import RocketCommand
from rocket_sensor_data import RocketSensorData
import RPi.GPIO as GPIO

from communication.data_compression import TelemetryObject

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

        # Start the main detection loop in a separate thread
        detection_thread = Thread(target=self._main_detection_loop, daemon=True)
        detection_thread.start()

        # Start main control loop
        self._main_telemetry_loop()

    def _main_telemetry_loop(self):
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
            
            # DPS
            telemetry_objects: list[TelemetryObject] = []
            dps_data = self._rocket_sensor_data.get_dps_data()
            if dps_data is not None and dps_data[1] is not None:
                dps_values = dps_data[1]
                telemetry_objects.append({"label": "dps.prs", "timestamp": current_timestamp, "data": dps_values["pressure"]})
                telemetry_objects.append({"label": "dps.tmp", "timestamp": current_timestamp, "data": dps_values["temperature"]})
                telemetry_objects.append({"label": "dps.alt", "timestamp": current_timestamp, "data": dps_values["altitude"]})

                # Send entire batch as single compressed transmission
                if telemetry_objects:
                    self._rocket_communication.send_data(("d2", telemetry_objects))

            # GPS
            telemetry_objects: list[TelemetryObject] = []
            gps_data = self._rocket_sensor_data.get_gps_data()
            if gps_data is not None and gps_data[1] is not None:
                gps_values = gps_data[1]
                telemetry_objects.append({"label": "gps.pos", "timestamp": current_timestamp, "data": gps_values["position"]})
                telemetry_objects.append({"label": "gps.alt", "timestamp": current_timestamp, "data": gps_values["altitude"]})
                telemetry_objects.append({"label": "gps.spd", "timestamp": current_timestamp, "data": gps_values["speed"]})
                telemetry_objects.append({"label": "gps.hdg", "timestamp": current_timestamp, "data": gps_values["heading"]})
                telemetry_objects.append({"label": "gps.sat", "timestamp": current_timestamp, "data": gps_values["satellites"]})

                # Send entire batch as single compressed transmission
                if telemetry_objects:
                    self._rocket_communication.send_data(("d3", telemetry_objects))

            # Camera
            # telemetry_objects: list[TelemetryObject] = []
            # cam_data = self._rocket_sensor_data.get_camera_data()
            # if cam_data is not None and cam_data[1] is not None:
            #     cam_values = cam_data[1]
            #     telemetry_objects.append({"label": "cam.fps", "timestamp": current_timestamp, "data": cam_values["image"]})
            #     telemetry_objects.append({"label": "cam.res", "timestamp": current_timestamp, "data": cam_values["resolution"]})
            #     telemetry_objects.append({"label": "cam.on", "timestamp": current_timestamp, "data": cam_values["is_on"]})

            #     # Send entire batch as single compressed transmission
            #     if telemetry_objects:
            #         self._rocket_communication.send_data(("d4", telemetry_objects))

            # Raspiberry Pi System Data
            telemetry_objects: list[TelemetryObject] = []
            rpi_data = self._rocket_sensor_data.get_rpi_data()
            if rpi_data is not None and rpi_data[1] is not None:
                rpi_values = rpi_data[1]

                # Section 1
                telemetry_objects.append({"label": "rasp.lat", "timestamp": current_timestamp, "data": rpi_values["latency"]})
                telemetry_objects.append({"label": "rasp.ram", "timestamp": current_timestamp, "data": rpi_values["ram_usage"]})
                telemetry_objects.append({"label": "rasp.cpu", "timestamp": current_timestamp, "data": rpi_values["cpu_usage"]})
                telemetry_objects.append({"label": "rasp.dsk", "timestamp": current_timestamp, "data": rpi_values["disk_usage"]})

                # Send entire batch as single compressed transmission
                if telemetry_objects:
                    self._rocket_communication.send_data(("d5", telemetry_objects))

                # Section 2
                telemetry_objects: list[TelemetryObject] = []
                telemetry_objects.append({"label": "rasp.vlt", "timestamp": current_timestamp, "data": rpi_values["input_voltage"]})
                telemetry_objects.append({"label": "rasp.pwr", "timestamp": current_timestamp, "data": rpi_values["input_power"]})
                telemetry_objects.append({"label": "rasp.tmp", "timestamp": current_timestamp, "data": rpi_values["temperature"]})
                telemetry_objects.append({"label": "rasp.upt", "timestamp": current_timestamp, "data": rpi_values["uptime"]})

                if telemetry_objects:
                    self._rocket_communication.send_data(("d6", telemetry_objects))

            # States
            telemetry_objects: list[TelemetryObject] = []
            has_parachute_deployed: bool = self._rocket_controller.is_co2_breach_triggered()
            if has_parachute_deployed:
                telemetry_objects.append({"label": "state.par", "timestamp": current_timestamp, "data": True})

            # LCD Status Display
            gps_data = self._rocket_sensor_data.get_gps_data()
            imu_is_valid = "OP" if imu_data is not None and imu_data[1] is not None else "ERR"
            dps_is_valid = "OP" if dps_data is not None and dps_data[1] is not None else "ERR"
            gps_is_valid = "OP" if gps_data is not None and gps_data[1] is not None else "ERR"
            piezo_is_valid = "ON" if self._rocket_controller._piezo.is_playing_tone else "OFF"
            self._rocket_controller._lcd.set_live_scrolling_text(f"STATE: READY  CON: 50ms  RTMP: 25°C", 0)
            self._rocket_controller._lcd.set_live_scrolling_text(
                f"DPS: {dps_is_valid}  IMU: {imu_is_valid}  GPS: {gps_is_valid}  CAM: OP  PIEZO: {piezo_is_valid} ", 1, delay=0.22)

            # Prevent flooding worker queues (LCD + radio) and reduce bus contention.
            time.sleep(0.1)


    def _add_command_listeners(self):
        """
        Add listeners for commands.
        """
        pass

    def _main_detection_loop(self):
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