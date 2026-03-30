from datetime import datetime

import rocket_controller
from rocket_gcs_communication import RocketCommunication
from rocket_controller import RocketController
from commands_list import RocketCommand
from rocket_sensor_data import RocketSensorData
import RPi.GPIO as GPIO

import time

class RocketComputer:
    def __init__(self):
        # Initialize Rocket GCS Communication
        self._rocket_communication = RocketCommunication()

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
            # IMU
            imu_data = self._rocket_sensor_data.get_imu_data()
            if imu_data is not None and imu_data[1] is not None:
                imu_values = imu_data[1]
                self._rocket_communication.send_data("imu.acc", (imu_data[0], imu_values["acceleration"]))
                self._rocket_communication.send_data("imu.anv", (imu_data[0], imu_values["gyro"]))
                self._rocket_communication.send_data("imu.mgn", (imu_data[0], imu_values["magnetometer"]))
                self._rocket_communication.send_data("imu.grv", (imu_data[0], imu_values["gravity"]))
                self._rocket_communication.send_data("imu.ori", (imu_data[0], imu_values["vector_orientation"]))
                self._rocket_communication.send_data("imu.lac", (imu_data[0], imu_values["linear_acceleration"]))
            
            # DPS
            dps_data = self._rocket_sensor_data.get_dps_data()
            if dps_data is not None and dps_data[1] is not None:
                dps_values = dps_data[1]
                self._rocket_communication.send_data("dps.prs", (dps_data[0], dps_values["pressure"]))
                self._rocket_communication.send_data("dps.alt", (dps_data[0], dps_values["altitude"]))
                self._rocket_communication.send_data("dps.tmp", (dps_data[0], dps_values["temperature"]))

            # GPS
            gps_data = self._rocket_sensor_data.get_gps_data()
            if gps_data is not None and gps_data[1] is not None:
                gps_values = gps_data[1]
                self._rocket_communication.send_data("gps.pos", (gps_data[0], (gps_values["latitude"], gps_values["longitude"])))
                self._rocket_communication.send_data("gps.alt", (gps_data[0], gps_values["altitude"]))

            # RASPI COMPUTER STATS
            raspi_computer_data = self._rocket_sensor_data.get_raspi_stats()
            # if raspi_computer_data is not None and raspi_computer_data[1] is not None:
            #     raspi_values = raspi_computer_data[1]
            #     self._rocket_communication.send_data("rasp.ram", (raspi_computer_data[0], raspi_values["ram_percent"]))
            #     self._rocket_communication.send_data("rasp.cpu", (raspi_computer_data[0], raspi_values["cpu_usage_percent"]))
            #     self._rocket_communication.send_data("rasp.dsk", (raspi_computer_data[0], raspi_values["disk_usage_percent"]))
            #     self._rocket_communication.send_data("rasp.tmp", (raspi_computer_data[0], raspi_values["cpu_temp"]))
            #     self._rocket_communication.send_data("rasp.vlt", (raspi_computer_data[0], raspi_values["voltage"]))
            #     self._rocket_communication.send_data("rasp.pwr", (raspi_computer_data[0], raspi_values["throttled"]))
            #     self._rocket_communication.send_data("rasp.upt", (raspi_computer_data[0], raspi_values["uptime"]))

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