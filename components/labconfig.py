import json
from functools import wraps

class LabConfig:
    def __init__(self):
        self.config = dict()
        with open("ui_parameters.json") as f:
            self.config = json.load(f)

    def update_config(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            func(*args, **kwargs)
            with open("ui_parameters.json", 'w') as f:
                json.dump(self.config, f, indent=4)
        return wrapper