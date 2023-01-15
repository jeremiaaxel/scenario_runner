import json


def get_sensors_json(filename: str = "sensors.json") -> list:
    """
    Get the sensors from the json file
    """
    with open(filename) as f:
        sensors = json.load(f)
        return sensors.get("sensors", None)