# Session Journal
# Log all actions with timestamps in JSONL format

# Session Journal
# Log all actions with timestamps in JSONL format
# This module logs actions with timestamps in a JSONL format.

def log_action(action):
    timestamp = time.time()
    log_entry = {
        "timestamp": timestamp,
        "action": action
    }
    # Log the action in JSONL format
    try:
        with open("session_log.jsonl", "a") as log_file:
            log_file.write(json.dumps(log_entry) + "\n")
    except IOError as e:
        print(f"Error logging action: {e}")

if __name__ == "__main__":
    # Example usage
    try:
        log_action("Started session")
        log_action("Performed validation")
    except Exception as e:
        print(f"Error: {e}")