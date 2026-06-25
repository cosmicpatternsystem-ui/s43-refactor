import platform
import os

class HardwareAbstractionLayer:
    def __init__(self):
        self.os_type = platform.system()
        self.architecture = platform.architecture()[0]

    def check_compatibility(self):
        """Check if the current OS and architecture are supported."""
        supported_os = ['Windows', 'Linux', 'Darwin']  # Darwin is for macOS
        if self.os_type not in supported_os:
            raise EnvironmentError(f"Unsupported OS: {self.os_type}")
        print(f"Running on {self.os_type} ({self.architecture}) - Compatibility check passed.")

    def run_command(self, command):
        """Run a system command based on the OS."""
        if self.os_type == 'Windows':
            os.system(command)
        else:
            os.system(command)

# Example usage
if __name__ == "__main__":
    hal = HardwareAbstractionLayer()
    hal.check_compatibility()