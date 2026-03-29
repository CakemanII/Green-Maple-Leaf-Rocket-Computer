import subprocess
import psutil

class RaspiController:
    def __init__(self):
        pass

    def _get_cpu_temp(self) -> float:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            temp = f.read()
        return float(temp) / 1000  # Convert millidegrees to °C

    def _get_voltage(self) -> float | None:
        try:
            output = subprocess.check_output(["vcgencmd", "measure_volts"])
            return float(output.decode().replace("volt=", "").replace("V\n", ""))
        except:
            return None

    def _get_throttled(self) -> str:
        try:
            output = subprocess.check_output(["vcgencmd", "get_throttled"])
            return output.decode().strip()
        except:
            return "N/A"
        
    def _get_uptime(self) -> float:
        with open("/proc/uptime", "r") as f:
            uptime_seconds = float(f.readline().split()[0])
        return uptime_seconds
    
    def _get_ram_usage(self) -> tuple[float, float]:
        ram = psutil.virtual_memory()
        ram_used = ram.used / (1024**2)  # MB
        ram_percent = ram.percent
        return ram_used, ram_percent

    def _get_cpu_usage(self) -> float:
        return psutil.cpu_percent(interval=0.1)
    
    def _get_disk_usage(self) -> float:
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent
        return disk_percent
    
    def get_raspi_stats(self) -> dict:
        return {
            "cpu_temp": self._get_cpu_temp(),
            "voltage": self._get_voltage(),
            "throttled": self._get_throttled(),
            "uptime": self._get_uptime(),
            "ram_used_mb": self._get_ram_usage()[0],
            "ram_percent": self._get_ram_usage()[1],
            "cpu_usage_percent": self._get_cpu_usage(),
            "disk_usage_percent": self._get_disk_usage()
        }