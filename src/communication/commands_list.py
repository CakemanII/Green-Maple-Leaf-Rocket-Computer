from enum import Enum

class RocketCommand(Enum):
    SET_ROCKET_FLIGHT_SESSION = "srfs"
    MANUAL_PARACHUTE_DEPLOYMENT = "mpd"
    TOGGLE_AUTOMATIC_DEPLOYMENT = "tad"
    SHUTDOWN_SYSTEM = "sd"
    TOGGLE_SENSOR_DATA_TRANSMISSION = "tstd"
    STOP_RECEIVING = "sr"
    TOGGLE_ONBOARD_RASPI_CAM = "torc"
