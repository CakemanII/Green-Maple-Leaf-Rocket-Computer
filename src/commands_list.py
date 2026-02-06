from enum import Enum

class RocketCommand(Enum):
    MANUAL_PARACHUTE_DEPLOYMENT = "mpd"
    TOGGLE_AUTOMATIC_DEPLOYMENT = "tad"
    SHUTDOWN_SYSTEM = "sd"
    TOGGLE_SENSOR_DATA_TRANSMISSION = "tstd"
    STOP_RECEIVING = "sr"
    TOGGLE_ONBOARD_RASPI_CAM = "torc"

class DataTransmissionLabels(Enum):
    ALTITUDE = "alt"
    PRESSURE = "pres"
    TEMPERATURE = "temp"
    HUMIDITY = "hum"
    GPS_COORDINATES = "gps"
    ACCELERATION = "acc"
    GYROSCOPE = "gyro"
