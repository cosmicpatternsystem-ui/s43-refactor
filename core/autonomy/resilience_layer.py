class ResilienceLayer:
    def __init__(self):
        self.state = "offline"  # Initial state can be offline or connected

    def set_state(self, state):
        """Set the operational state of the resilience layer."""
        if state in ["offline", "connected"]:
            self.state = state
        else:
            raise ValueError("State must be 'offline' or 'connected'.")

    def get_state(self):
        """Return the current operational state."""
        return self.state

    def handle_offline(self):
        """Handle operations in offline state."""
        return "Resilience layer is in offline mode."

    def handle_connected(self):
        """Handle operations in connected state."""
        return "Resilience layer is in connected mode."

    def reset(self):
        """Reset the resilience layer to its initial state."""
        self.state = "offline"