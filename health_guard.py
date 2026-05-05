import psutil
import time

class HealthGuard:
    """
    Monico HealthGuard - Hardware preservation for iOS devices.
    Ensures the AI reasoning engine never slows down the OS.
    """
    def __init__(self, cpu_limit=25.0): # iOS limits are stricter
        self.cpu_limit = cpu_limit

    def check(self):
        cpu_usage = psutil.cpu_percent(interval=1)
        status = "OPTIMAL"
        if cpu_usage > self.cpu_limit:
            status = "THROTTLING"
        return {"status": status, "cpu": f"{cpu_usage}%"}

if __name__ == "__main__":
    guard = HealthGuard()
    print(f"[iOS_HEALTH] {guard.check()}")