class CoreAutonomyEngine:
    def __init__(self):
        self.safety_governor = SafetyGovernor()
        self.current_phase = 1  # Start at phase 1
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

    def execute_phase(self, phase):
        """Execute the logic for the given phase."""
        print(f"Starting execution for Phase {phase['phase']}: {phase['description']}")
        if self.safety_governor.is_within_bounds(phase['status']):
            print(f"Executing Phase {phase['phase']}: {phase['description']}")
            print("Phase execution started.")
            # Update phase status to 'in progress'
            phase['status'] = 'in progress'
            print("Phase execution completed successfully.")
        else:
            print(f"Phase {phase['phase']} is out of bounds!")

    def reset(self):
        """Reset the engine to its initial state."""
        self.state = "offline"