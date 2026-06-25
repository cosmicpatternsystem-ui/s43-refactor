class CoreAutonomyEngine:
    def __init__(self):
        self.state = "offline"  # Initial state can be offline or connected

    def set_state(self, state):
        """Set the operational state of the engine."""
        if state in ["offline", "connected"]:
            self.state = state
        else:
            raise ValueError("State must be 'offline' or 'connected'.")

    def get_state(self):
        """Return the current operational state."""
        return self.state

    def process_data(self, data):
        """Process incoming data based on the current state."""
        if self.state == "connected":
            # Process data in connected state
            return f"Processing data: {data}"
        else:
            return "Engine is offline. Cannot process data."

    def reset(self):
        """Reset the engine to its initial state."""
        self.state = "offline"