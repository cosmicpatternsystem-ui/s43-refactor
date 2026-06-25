class SafetyGovernor:
    def __init__(self):
        # Hard-coded safety bounds
        self.lower_bound = 0.0
        self.upper_bound = 100.0

    def is_within_bounds(self, value):
        """Check if the value is within the safety bounds."""
        return self.lower_bound <= value <= self.upper_bound

    def get_bounds(self):
        """Return the safety bounds."""
        return self.lower_bound, self.upper_bound