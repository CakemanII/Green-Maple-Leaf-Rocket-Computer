import time
import board
import busio
import serial

from datetime import datetime

import pynmea2
import adafruit_dps310
from adafruit_bno08x.i2c import BNO08X_I2C
from adafruit_bno08x import (
    BNO_REPORT_ACCELEROMETER,
    BNO_REPORT_GYROSCOPE,
    BNO_REPORT_MAGNETOMETER,
    BNO_REPORT_ROTATION_VECTOR,
)

import adafruit_rfm9x
import digitalio

# I2C SETUP
# Initialize the I2C bus using Raspberry Pi hardware pins (SCL/SDA)
i2c = busio.I2C(board.SCL, board.SDA)

# Give sensors time to power up and stabilize
time.sleep(1.5)

# region DPS310 SETUP
# Initialize DPS310 pressure/temperature sensor
dps = adafruit_dps310.DPS310(i2c)
# Set reference sea-level pressure for altitude calculation
dps.sea_level_pressure = 1013.25
# endregion

# region GPS SETUP (RAW NMEA)
# Serial port used by the GPS module
PORT = "/dev/ttyAMA0"
BAUD = 9600
prev_gps_text = ""

# Open serial connection to GPS
ser = serial.Serial(PORT, BAUD, timeout=1)
# endregion

# region RFM9X SETUP
# RFM9x LoRa Radio setup
# SPI bus
spi = busio.SPI(board.SCK, board.MOSI, board.MISO)

# Chip select (CE1)
cs = digitalio.DigitalInOut(board.CE1)
cs.direction = digitalio.Direction.OUTPUT

# Reset pin
reset = digitalio.DigitalInOut(board.D25)
reset.direction = digitalio.Direction.OUTPUT
reset.value = True

# DIO0 / G0 interrupt pin
dio0 = digitalio.DigitalInOut(board.D5)
dio0.direction = digitalio.Direction.INPUT

rfm9x = None

# region BNO08X SETUP & IMU CALIBRATION
# Create BNO08X IMU object
bno = BNO08X_I2C(i2c)

bno.enable_feature(BNO_REPORT_ACCELEROMETER)
bno.enable_feature(BNO_REPORT_GYROSCOPE)
bno.enable_feature(BNO_REPORT_MAGNETOMETER)
bno.enable_feature(BNO_REPORT_ROTATION_VECTOR)

print("Calibrating IMU — keep sensor still")

# Allow time for the sensor to settle before calibration
time.sleep(2)

# Number of samples used to compute calibration offsets
SAMPLES = 400

# Accumulators for accelerometer and gyroscope readings
ax = ay = az = 0.0
gx = gy = gz = 0.0

# Collect samples while the sensor is stationary
for _ in range(SAMPLES):
    a = bno.acceleration  # Acceleration in m/s²
    g = bno.gyro          # Angular velocity in rad/s

    ax += a[0]
    ay += a[1]
    az += a[2]

    gx += g[0]
    gy += g[1]
    gz += g[2]

    # Small delay to control sampling rate
    time.sleep(0.005)

# Compute average accelerometer offsets
# Z-axis offset removes gravity (9.80665 m/s²)
accel_offset = (
    ax / SAMPLES,
    ay / SAMPLES,
    (az / SAMPLES) - 9.80665
)

# Compute average gyroscope offsets (drift)
gyro_offset = (
    gx / SAMPLES,
    gy / SAMPLES,
    gz / SAMPLES
)

print("IMU calibrated")
# endregion

# =========================
# MAIN LOOP
# =========================
print("\nLive sensor data (Ctrl+C to stop)\n")
prev_gps_text = ""

class SensorData:
    @staticmethod
    def get_bno_data() -> object:
        ax, ay, az = bno.acceleration
        gx, gy, gz = bno.gyro
        mx, my, mz = bno.magnetic
        quat_i, quat_j, quat_k, quat_real = bno.quaternion
        return {
            "acceleration": (ax, ay, az),
            "gyroscope": (gx, gy, gz),
            "magnetometer": (mx, my, mz),
            "quaternion": (quat_i, quat_j, quat_k, quat_real)
        }
    
    @staticmethod
    def get_dps_data() -> object:
        pressure = dps.pressure
        altitude = dps.altitude
        temperature = dps.temperature
        return {
            "pressure": pressure,
            "altitude": altitude,
            "temperature": temperature
        }
    
    @staticmethod
    def get_gps_output(ser: serial.Serial, prev_gps_text: str) -> str:
        # Default GPS status when no fix is available
        gps_text = "NO FIX" if prev_gps_text == "" else prev_gps_text

        try:
            # Read one NMEA sentence from the GPS
            line = ser.readline().decode("ascii", errors="replace")

            # Process GPGGA sentences (contain fix data)
            if line.startswith("$GPGGA"):
                msg = pynmea2.parse(line)

                # gps_qual > 0 indicates a valid GPS fix
                if msg.gps_qual > 0:
                    gps_text = (
                        f"{msg.latitude:.6f},{msg.longitude:.6f} "
                        f"{msg.altitude}m {msg.num_sats}sats"
                    )
                    prev_gps_text = gps_text

        except pynmea2.ParseError:
            # Ignore malformed NMEA sentences
            return None
        
        return gps_text


class Transmitter:
    @staticmethod
    def verify_rfm9x():
        global rfm9x
        rfm9x = None
        print("Checking for RFM9x module...")
        while True:
            time.sleep(0.1)
            try:
                rfm9x = adafruit_rfm9x.RFM9x(
                    spi,
                    cs,
                    reset,
                    915.0,
                )
                print("✅ RFM9x detected!")
                break
            except RuntimeError as e:
                print("❌ RFM9x NOT DETECTED")

    @staticmethod
    def send_data(data: str) -> str:
        global rfm9x
        try:
            # Transmission
            now = datetime.now()
            timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
            packet = bytes({"t": timestamp, "d": data}.__str__(), "utf-8")
            rfm9x.send(packet)
            return "Sent: {}{}".format(packet[:25], "" if len(packet) < 25 else "...")
        except Exception as e:
            print("\n"*10 + "Error occurred: {}".format(e))
            Transmitter.verify_rfm9x()
            return "Failed to send data. RFM9x re-initialized."


class Display:
    @staticmethod
    def get_and_print_sensor_data() -> None:
        global prev_gps_text
        # ---- IMU ----
        # Read raw acceleration and gyroscope data
        bno_data = SensorData.get_bno_data()
        ax, ay, az = bno_data["acceleration"]
        gx, gy, gz = bno_data["gyroscope"]
        mx, my, mz = bno_data["magnetometer"]
        quat_i, quat_j, quat_k, quat_real = bno_data["quaternion"]

        # Apply calibration offsets to accelerometer
        ax -= accel_offset[0]
        ay -= accel_offset[1]
        az -= accel_offset[2]

        # Apply calibration offsets to gyroscope
        gx -= gyro_offset[0]
        gy -= gyro_offset[1]
        gz -= gyro_offset[2]

        # ---- DPS310 ----
        # Read pressure (hPa), altitude (m), and temperature (°C)
        dps_data = SensorData.get_dps_data()
        pressure = dps_data["pressure"]
        altitude = dps_data["altitude"]
        temperature = dps_data["temperature"]

        # ---- GPS ----
        new_gps_text = SensorData.get_gps_output(ser, prev_gps_text)
        if new_gps_text is not None:
            gps_text = new_gps_text
            prev_gps_text = new_gps_text
        else:
            gps_text = prev_gps_text

        # Send data via RFM9x
        results = Transmitter.send_data(
            f"ACC:{ax:.2f},{ay:.2f},{az:.2f};"
            f"GYRO:{gx:.3f},{gy:.3f},{gz:.3f};"
            f"MAG:{mx:.1f},{my:.1f},{mz:.1f};"
            f"QUAT:{quat_i:.3f},{quat_j:.3f},{quat_k:.3f},{quat_real:.3f};"
            f"DPS:{pressure:.2f},{altitude:.2f},{temperature:.1f};"
            f"GPS:{gps_text}"
        )

        # ---- IN-PLACE MULTI-LINE OUTPUT ----
        # Print all sensor data on separate lines, overwriting previous output
        output_lines = [
            f"ACC [m/s²]:    {ax:7.2f}  {ay:7.2f}  {az:7.2f}",
            f"GYRO [rad/s]:  {gx:7.3f}  {gy:7.3f}  {gz:7.3f}",
            f"MAG [uT]:      {mx:7.1f}  {my:7.1f}  {mz:7.1f}",
            f"QUAT:          {quat_i:7.3f}  {quat_j:7.3f}  {quat_k:7.3f}  {quat_real:7.3f}",
            "",
            f"Pressure:      {pressure:7.2f} hPa",
            f"Altitude:      {altitude:7.2f} m",
            f"Temperature:   {temperature:5.1f} °C",
            "",
            f"GPS: {gps_text:<50}",
            "",
            f"TX: {results:<60}"
        ]

        # Move cursor up to overwrite previous output (if not first loop)
        if 'printed_once' in globals():
            print(f"\033[{len(output_lines)}A", end="")  # ANSI: move cursor up
        else:
            global printed_once
            printed_once = True

        print("\n".join(output_lines), flush=True)

# Verify RFM9x presence before entering main loop
Transmitter.verify_rfm9x()

while True:
    # Display sensor data
    Display.get_and_print_sensor_data()

    # Control update rate
    time.sleep(0.1)