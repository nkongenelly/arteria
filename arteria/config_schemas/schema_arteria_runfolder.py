runfolder_schema = {
    "type": "object",
    "properties": {
        "monitored_directories": {
            "type": "array",
            "items": {
                "type": "string",
                "minLength": 1,
            },
            "minItems": 1,
        },
        "completed_marker_grace_minutes": {
            "type": "number",
        },
        "port": {
            "type": "number",
        },
        "logger_config_file": {
            "type": "string",
            "minLength": 1,
        }
    },
    "required": [
        "monitored_directories",
        "completed_marker_grace_minutes",
        "port",
        "logger_config_file",
    ]
}
