import sys
import toml

def update_version(version):
    file_path = 'pyproject.toml'
    with open(file_path, 'r') as f:
        data = toml.load(f)
    
    # Update version
    data['project']['version'] = version

    with open(file_path, 'w') as f:
        toml.dump(data, f)
    
    print(f"Version updated to {version}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python update_version.py <new_version>")
        sys.exit(1)

    new_version = sys.argv[1]
    update_version(new_version)
