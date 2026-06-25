import random
import time

class ChaosMonkey:
    def __init__(self, modules):
        self.modules = modules

    def disable_module(self, module):
        """Simulate disabling a module."""
        print(f"Disabling module: {module}")
        # Here you would implement the actual logic to disable the module

    def run(self):
        """Randomly disable modules to test the Self-Healer's response."""
        while True:
            module_to_disable = random.choice(self.modules)
            self.disable_module(module_to_disable)
            time.sleep(random.randint(1, 5))  # Wait for a random time before disabling another module

# Example usage
if __name__ == "__main__":
    modules = ['self_healer', 'sanction_proof_relay', 'cli_monitor']
    chaos_monkey = ChaosMonkey(modules)
    chaos_monkey.run()