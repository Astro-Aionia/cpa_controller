import requests
import json

class RemoteCPA:
    def __init__(self, host: str, port: int, max_retries=3):
        self.host = host
        self.port = port
        self.max_retries = max_retries
        self.api_url = f"http://{self.host}:{self.port}"

    def apiget(self, command):
        for i in range(self.max_retries):
            try:
                apicall = self.api_url + command
                response = requests.get(apicall)
                rc = response.content.decode()
                return json.loads(rc)
            except requests.exceptions.ConnectionError as err:
                print(err)
        print(f"Failed to connect to CPA API after {self.max_retries} attempts.")
        raise requests.exceptions.ConnectionError
    
    def apiput(self, command, value):
        for i in range(self.max_retries):
            try:
                apicall = self.api_url + command
                response = requests.put(apicall, json={'value': value})
                rc = response.content.decode()
                return json.loads(rc)
            except requests.exceptions.ConnectionError as err:
                print(err)
        print(f"Failed to connect to CPA API after {self.max_retries} attempts.")
        raise requests.exceptions.ConnectionError
    
if __name__ == "__main__":
    remote = RemoteCPA(host="127.0.0.1", port=49900)

    import time
    start_time = time.time()
    rc = remote.apiput("/settings/232/", value='1')
    end_time = time.time()
    print(end_time-start_time)

    print(rc)