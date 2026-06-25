import json

class CLIMonitor:
    def __init__(self, roadmap_file):
        self.roadmap_file = roadmap_file
        self.phases = self.load_roadmap()

    def load_roadmap(self):
        """Load the roadmap from the specified JSON file."""
        with open(self.roadmap_file, 'r') as file:
            try:
                roadmap = json.load(file)
            except json.JSONDecodeError as e:
                print(f"Error loading JSON: {e}")
                roadmap = []  # Fallback to an empty roadmap or handle as needed
            return roadmap['phases']

    def display_progress(self):
        """Display the progress of the roadmap phases."""
        print("Roadmap Progress:")
        for phase in self.phases:
            print(f"Phase {phase['phase']}: {phase['description']}")

    def update_phase(self, phase_number, status):
        """Update the status of a specific phase."""
        for phase in self.phases:
            if phase['phase'] == phase_number:
                phase['status'] = status
                break

    def save_progress(self):
        """Save the updated roadmap back to the JSON file."""
        with open(self.roadmap_file, 'w') as file:
            json.dump({"phases": self.phases}, file, indent=4)

# Example usage
if __name__ == "__main__":
    monitor = CLIMonitor('roadmap/master_plan.json')
    monitor.display_progress()