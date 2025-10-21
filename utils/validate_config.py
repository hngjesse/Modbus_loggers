import json
import sys
from jsonschema import validate, ValidationError

# --- JSON schema definition ---
schema = {
    "type": "object",
    "properties": {
        "modbus": {
            "type": "object",
            "properties": {
                "type": {"enum": ["tcp", "serial"]},

                # TCP parameters
                "host": {"type": "string"},
                "port": {"type": "integer"},

                # Serial parameters
                "baudrate": {"type": "integer"},
                "timeout": {"type": "number"},
                "stopbits": {"type": "integer"},
                "bytesize": {"type": "integer"},
                "parity": {"type": "string"},
                "port": {"type": ["string", "integer"]}
            },
            "required": ["type", "timeout"],
            "oneOf": [
                {   # Case 1: TCP
                    "properties": {
                        "type": {"const": "tcp"},
                        "host": {"type": "string"},
                        "port": {"type": "integer"}
                    },
                    "required": ["type", "host", "port"]
                },
                {   # Case 2: Serial
                    "properties": {
                        "type": {"const": "serial"},
                        "port": {"type": "string"},
                        "baudrate": {"type": "integer"},
                        "stopbits": {"type": "integer"},
                        "bytesize": {"type": "integer"},
                        "parity": {"type": "string"}
                    },
                    "required": ["type", "port", "baudrate", "stopbits", "bytesize", "parity"]
                }
            ]
        },

        "device": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "start_addr": {"type": "integer"},
                "reg_count": {"type": "integer"},
                "id_range": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "minItems": 1
                }
            },
            "required": ["name", "start_addr", "reg_count", "id_range"]
        },

        "logging": {
            "type": "object",
            "properties": {
                "base_folder": {"type": "string"},
                "log_retention_days": {"type": "integer"},
                "file_suffix": {"type": "string"},
                "header": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 0
                },
                "time_step": {"type": "number"}
            },
            "required": ["base_folder", "log_retention_days", "file_suffix", "header", "time_step"]
        }
    },
    "required": ["modbus", "device", "logging"]
}

# --- Validator function ---
def validate_config(config_path: str) -> dict:
    """Validate and return JSON config, with robust error handling."""

    # --- Check file existence first ---
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
    except FileNotFoundError:
        print(f"❌ Config file not found: {config_path}")
        sys.exit(1)
    except PermissionError:
        print(f"❌ Permission denied when trying to read: {config_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ JSON syntax error in {config_path}: {e}")
        sys.exit(1)

    # --- Schema validation ---
    try:
        validate(instance=config, schema=schema)
    except ValidationError as e:
        print(f"❌ Invalid config: {e.message}")
        sys.exit(1)

    print(f"✅ Config file '{config_path}' validated successfully.")
    return config

# --- If run directly ---
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python validate_config.py <config_path>")
        sys.exit(1)
    config_path = sys.argv[1]
    validate_config(config_path)