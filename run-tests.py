import os
import subprocess

# Directories with test files
ill_typed_dir = "tests/ill-typed"
well_typed_dir = "tests/well-typed"
interpret_script = "src/interpret.py"

def run_test(filepath, expected_exit_code):
    """Runs the interpret script on a given file and checks the exit code."""
    result = subprocess.run(["python", interpret_script, filepath], capture_output=True)
    if result.returncode == expected_exit_code:
        print(f"SUCCESS: {filepath}")
    else:
        print(f"FAIL: {filepath}")
        print(f"Expected exit code {expected_exit_code}, got {result.returncode}")
        print("Output:")
        print(result.stderr.decode() if result.stderr else result.stdout.decode())

def main():
    # Test ill-typed files (expected to fail with exit code 1)
    for filename in os.listdir(ill_typed_dir):
        filepath = os.path.join(ill_typed_dir, filename)
        if os.path.isfile(filepath):
            run_test(filepath, expected_exit_code=1)

    # Test well-typed files (expected to succeed with exit code 0)
    for filename in os.listdir(well_typed_dir):
        filepath = os.path.join(well_typed_dir, filename)
        if os.path.isfile(filepath):
            run_test(filepath, expected_exit_code=0)

if __name__ == "__main__":
    main()
