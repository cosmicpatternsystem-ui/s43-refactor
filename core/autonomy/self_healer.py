import os

class SelfHealer:
    def __init__(self, file_paths):
        self.file_paths = file_paths

    def check_file(self, file_path):
        """Check if the file is corrupted."""
        return not os.path.exists(file_path) or os.path.getsize(file_path) == 0

    def repair_file(self, file_path):
        """Repair the corrupted file by recreating it."""
        with open(file_path, 'w') as f:
            f.write("File has been restored to a healthy state.")
        return f"Repaired: {file_path}"

    def heal(self):
        """Check and repair all specified files."""
        repaired_files = []
        for file_path in self.file_paths:
            if self.check_file(file_path):
                repaired_files.append(self.repair_file(file_path))
        return repaired_files