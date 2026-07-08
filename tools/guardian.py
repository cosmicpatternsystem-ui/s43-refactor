# Guardian.py
# Validation logic for encoding, syntax, and secret scanning

# Removed chardet dependency
import ast
import re

def validate_encoding(file_path):
    with open(file_path, 'rb') as f:
        rawdata = f.read()
    # Check for UTF-8 without BOM
    if not rawdata.startswith(b'\xef\xbb\xbf'):
        try:
            rawdata.decode('utf-8')
        except UnicodeDecodeError:
            raise ValueError(f"File {file_path} is not UTF-8 encoded.")

def validate_syntax(file_path):
    with open(file_path, 'r', newline='') as f:
        source = f.read()
    try:
        ast.parse(source)
    except SyntaxError as e:
        raise SyntaxError(f"Syntax error in {file_path}: {e}")

def secret_scan(file_path):
    with open(file_path, 'r', newline='') as f:
        content = f.read()
    secrets = re.findall(r'(?i)(password|secret|token)\s*=\s*["\']?([^"\']+)["\']?', content)
    if secrets:
        raise ValueError(f"Secrets found in {file_path}: {secrets}")

if __name__ == "__main__":
    # Example usage
    try:
        validate_encoding("example_file.txt")
        validate_syntax("example_file.txt")
        secret_scan("example_file.txt")
    except Exception as e:
        print(f"Error: {e}")