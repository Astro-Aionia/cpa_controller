import requests
from functools import wraps

def ignore_connection_error(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            res = func(*args, **kwargs)
            return res
        except requests.exceptions.ConnectionError:
            print(f"Connection error in {func.__name__}, ignoring.")
            return None
    return wrapper
