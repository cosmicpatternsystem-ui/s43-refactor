class SafetyGovernor:
    def is_within_bounds(self, status):
        # Default safety check for Gold Standard
        return True

class CoreAutonomyEngine:
    def __init__(self):
        self.safety_governor = SafetyGovernor()
        self.current_phase = 1
        self.state = "offline"

    def set_state(self, state):
        if state in ["offline", "connected"]:
            self.state = state
        else:
            raise ValueError("State must be 'offline' or 'connected'.")

    def get_state(self):
        return self.state

    def execute_phase(self, phase):
        print(f"Starting execution for Phase {phase['phase']}: {phase['description']}")
        if self.safety_governor.is_within_bounds(phase['status']):
            print(f"Executing Phase {phase['phase']}: {phase['description']}")
            phase['status'] = 'in progress'
            print("Phase execution completed successfully.")
        else:
            print(f"Phase {phase['phase']} is out of bounds!")

    def reset(self):
        self.state = "offline"
