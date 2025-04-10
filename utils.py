import os
import json

def read_json_file(filepath):
    if not os.path.exists(filepath):
        return {}
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

def write_json_file(data, filepath):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=4)