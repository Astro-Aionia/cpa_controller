import time
import serial
import json
from functools import wraps

class CPA:
    def __init__(self, port, baudrate=9600, timeout=1, bit=8, parity='N', stop=1):
        self.ser = serial.Serial(port, baudrate, timeout=timeout, bytesize=bit, parity=parity, stopbits=stop)
        self.parameters = {}
        with open('cpa_parameters.json', 'r') as f:
            self.parameters = json.load(f)
        if not self.ser.is_open:
            self.ser.open()
        # self.init_parameters()

    def  __del__(self):
        if self.ser.is_open:
            self.ser.close()

    def cmd(self, command: str):
        self.ser.write((command + '\r').encode('ascii'))
        response = self.ser.readline().decode().strip()
        if ',' in response:
            response = response.split(',', 1)[1]
        if all(c in '01' for c in response.strip()) and len(response.strip()) in [8, 16, 32]:  # Check if the response is a binary string of length 8, 16, or 32
            return response
        try:
            return float(response) if '.' in response else int(response)
        except ValueError:
            return response
    
    def remote_error(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            remote_status = self.cmd("232")
            warning_status = int(self.cmd("WAR"),2)  # Convert the binary string to an integer
            # warning_status = 0
            # print(remote_status, warning_status)
            if remote_status == "OFF":
                raise Exception("CPA controller is in local control mode. Please switch to remote control mode to execute this command.")
            if warning_status != 0:
                raise Exception(f"CPA controller has a warning: {warning_status}. Please check the device and resolve the issue before executing this command.")
            return func(self, *args, **kwargs)
        return wrapper

    # @remote_error
    def get_parameter(self, param_name: str, channel=''):
        if param_name in self.parameters.keys():
            if param_name == "DLY":
                if channel not in "ABCDEF":
                    raise ValueError("Channel must be specified as A-F for parameter 'DLY'.")
                else:
                    channel_index = ord(channel) - ord('A')
                    self.parameters[param_name][channel_index] = self.cmd(f"{param_name} {channel}")
                    with open('cpa_parameters.json', 'w') as f:
                        json.dump(self.parameters, f, indent=4)
                    print(f"Parameter '{param_name}' for channel '{channel}' updated: {self.parameters[param_name][channel_index]}")
                    return self.parameters[param_name][channel_index]
            else:
                self.parameters[param_name] = self.cmd(param_name)
                with open('cpa_parameters.json', 'w') as f:
                    json.dump(self.parameters, f, indent=4)
                print(f"Parameter '{param_name}' updated: {self.parameters[param_name]}")
                return self.parameters[param_name]
        else:
            raise ValueError(f"Parameter '{param_name}' not found in parameters.")

    # @remote_error    
    def set_parameter(self, param_name: str, channel='', value=None):
        if param_name in self.parameters.keys():
            if param_name == "DLY":
                if channel not in "ABCDEF":
                    raise ValueError("Channel must be specified as A-F for parameter 'DLY'.")
                else:
                    self.cmd(f"{param_name} {channel},{value}")
                    self.get_parameter(param_name, channel)  # Update the parameter value in the class
            elif param_name == "RUN" or param_name == "GAT":
                if channel not in "ABCDEF":
                    raise ValueError(f"Channel must be specified as A-F for parameter '{param_name}'.")
                else:
                    self.cmd(f"{param_name} {channel},{value}")
                    self.get_parameter(param_name)  # Update the parameter value in the class
            else:
                self.cmd(f"{param_name} {value}")
                self.get_parameter(param_name)  # Update the parameter value after setting it
        else:
            raise ValueError(f"Parameter '{param_name}' not found in parameters.")
        
    def init_parameters(self):
        print("Initializing parameters from devices to python class...")
        for param_name in self.parameters.keys():
            if param_name == "DLY":
                for channel in "ABCDEF":
                    self.get_parameter(param_name, channel)
            else:
                self.get_parameter(param_name)
        print("All parameters updated.")
        
    def open(self):
        if self.get_parameter(param_name="232") == "ON":
            print("CPA controller is already in remote control mode.")
        else:
            self.set_parameter(param_name="232", value=1)
            print("CPA controller is now in remote control mode.")
        self.init_parameters()

    def close(self):
        if self.get_parameter(param_name="232") == "OFF":
            print("CPA controller is already in local control mode.")
        else:
            self.set_parameter(param_name="232", value=0)
            print("CPA controller is now in local control mode.")

    # @remote_error
    def set_current_safely(self, laser: int, current: int):
        if current < 0:
            raise ValueError("Current must be non-negative.")
        
        if laser == 1:
            cmd = "CUR"
        elif laser == 2:
            cmd = "C2R"
        else:
            raise ValueError("Laser must be 1 or 2.")
        
        self.get_parameter(param_name="SHU") # Check if the shutter is open
        if self.parameters["SHU"] == "OFF":
            self.set_parameter(param_name=cmd, value=current)
        else:
            self.get_parameter(param_name=cmd)
            if self.parameters[cmd] >= current:
                self.set_parameter(param_name=cmd, value=current)
                time.sleep(3)
                self.get_parameter(param_name=cmd)
            else:
               while self.get_parameter(param_name=cmd) < current:
                   self.set_parameter(param_name=cmd, value=self.get_parameter(param_name=cmd) + 1)
                   time.sleep(5)  # Adjust the sleep time as needed
    
    # @remote_error
    def laser_on_safely(self):
        self.get_parameter(param_name="LSR") # Check if the laser is already on
        self.get_parameter(param_name="SHU") # Check if the shutter is open
        if self.parameters["SHU"] == "ON":
            raise Exception("Shutter is already open.")
        else:
            print("Turning on the laser safely, please wait...")
            # First, make sure the laser is off
            # self.set_parameter(param_name="LSR", value=0)
            self.set_parameter(param_name="SHU", value=0)
            # Second, save the setting currents to buffer
            current1_to_set = self.get_parameter(param_name="CUS")
            current2_to_set = self.get_parameter(param_name="C2S")
            # Third, set the currents to 0
            self.set_parameter(param_name="CUR", value=0)
            self.set_parameter(param_name="C2R", value=0)
            # Fourth, turn on the laser
            self.set_parameter(param_name="LSR", value=1)
            self.set_parameter(param_name="SHU", value=1)
            # Finally, raise the currents to the setting values graduall
            i = 0
            while self.get_parameter(param_name="CUR") < current1_to_set:
                if i <= 10:
                    self.set_parameter(param_name="CUR", value=self.get_parameter(param_name="CUR") + 2)
                else:
                    self.set_parameter(param_name="CUR", value=self.get_parameter(param_name="CUR") + 1)
                time.sleep(5)  # Adjust the sleep time as needed
                i = i + 1
            i = 0
            while self.get_parameter(param_name="C2R") < current2_to_set:
                if i <= 10:
                    self.set_parameter(param_name="C2R", value=self.get_parameter(param_name="C2R") + 2)
                else:
                    self.set_parameter(param_name="C2R", value=self.get_parameter(param_name="C2R") + 1)
                time.sleep(5)  # Adjust the sleep time as needed
                i = i + 1 
            
comport = 'COM14'

cpa = CPA(port=comport)

if __name__ == "__main__":

    cpa.set_parameter(param_name="QRF", value="0")