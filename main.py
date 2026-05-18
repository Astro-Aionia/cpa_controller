from PyQt6 import QtWidgets
from PyQt6.QtWidgets import QApplication, QWidget, QMainWindow
from channel import Ui_Channel
from mainwindow import Ui_MainWindow

from remote import RemoteCPA

import sys
from functools import wraps
import json
import requests

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

class DelayChannel(QWidget, Ui_Channel):
    def __init__(self, channel: str, lcfg: LabConfig, remote: RemoteCPA):
        super().__init__()
        self.setupUi(self)
        self.channel = channel
        self.channelLabel.setText(f"Channel {channel}")
        self.lcfg = lcfg
        self.channel_config = self.lcfg.config["Puckel Cell"][self.channel]
        update_config = self.lcfg.update_config
        self.remote = remote

        if self.channel_config["Enabled"]:
                self.channelSwitchButton.setText("Disable")
                self.channelLabel.setStyleSheet("color: green;")
        else:
            self.channelSwitchButton.setText("Enable")
            self.channelLabel.setStyleSheet("color: black;")

        self.delayEdit.setText(str(self.channel_config["Value"]))
        self.delayIntervalEdit.setText(str(self.channel_config["Increment"]))

        @ignore_connection_error
        @update_config
        @self.update_ui
        def switch_channel(button_status: bool):
            if self.channel_config["Enabled"]:
                self.remote.apiput(f"/settings/RUN/{self.channel}/", value="1")
                self.channel_config["Enabled"] = False
            else:
                self.remote.apiput(f"/settings/RUN/{self.channel}/", value="0")
                self.channel_config["Enabled"] = True

        self.channelSwitchButton.clicked.connect(switch_channel)

        @ignore_connection_error
        @update_config
        @self.update_ui
        def set_delay(button_status: bool):
            delay_to_set = float(self.delayEdit.text())
            str_to_sent = str(int(delay_to_set*10)).zfill(7)
            rc = self.remote.apiput(f"/settings/DLY/{self.channel}/", str_to_sent)
            # rc = self.remote.apiget(f"/DLY/{self.channel}/")
            self.channel_config["Value"] = rc["DLY"][ord(self.channel) - ord('A')]

        self.delaySetButton.clicked.connect(set_delay)

        @self.update_ui
        def set_delay_increment(lineEdit_status=None):
            delay_increment_to_set = float(self.delayIntervalEdit.text())
            self.channel_config["Increment"] = delay_increment_to_set

        self.delayIntervalEdit.editingFinished.connect(set_delay_increment)

        @ignore_connection_error
        @update_config
        @self.update_ui
        def delay_increase(button_status: bool):
            delay_to_set = self.channel_config["Value"] + self.channel_config["Increment"]
            str_to_sent = str(int(delay_to_set*10)).zfill(7)
            rc = self.remote.apiput(f"/settings/DLY/{self.channel}/", str_to_sent)
            # rc = self.remote.apiget(f"/DLY/{self.channel}/")
            self.channel_config["Value"] = rc["DLY"][ord(self.channel) - ord('A')]

        self.delayIncreaseButton.clicked.connect(delay_increase)

        @ignore_connection_error
        @update_config
        @self.update_ui
        def delay_decrease(button_status: bool):
            delay_to_set = self.channel_config["Value"] - self.channel_config["Increment"]
            str_to_sent = str(int(delay_to_set*10)).zfill(7)
            rc = self.remote.apiput(f"/settings/DLY/{self.channel}/", str_to_sent)
            # rc = self.remote.apiget(f"/DLY/{self.channel}/")
            self.channel_config["Value"] = rc["DLY"][ord(self.channel) - ord('A')]
            
        self.delayDecreaseButton.clicked.connect(delay_decrease)

    def update_ui(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            func(*args, **kwargs)
            if self.channel_config["Enabled"]:
                self.channelSwitchButton.setText("Disable")
                self.channelLabel.setStyleSheet("color: green;")
            else:
                self.channelSwitchButton.setText("Enable")
                self.channelLabel.setStyleSheet("color: black;")

            self.delayEdit.setText(str(self.channel_config["Value"]))
            self.delayIntervalEdit.setText(str(self.channel_config["Increment"]))
        return wrapper

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, lcfg: LabConfig):
        super().__init__()
        self.setupUi(self)
        self.lcfg = lcfg
        self.remote = RemoteCPA(host=self.lcfg.config["Host"], port=self.lcfg.config["Port"])
        update_config = self.lcfg.update_config
        self.channels = [None, None, None, None, None, None]

        # setup channels
        widgetlist = [self.widget_A, self.widget_B, self.widget_C, self.widget_D, self.widget_E, self.widget_F]
        for i, channel in enumerate(['A', 'B', 'C', 'D', 'E', 'F']):
            self.channels[i] = DelayChannel(channel=channel, lcfg=self.lcfg, remote=self.remote)
            b = QtWidgets.QGridLayout(widgetlist[i])
            b.addWidget(self.channels[i])

        # init ui
        if self.lcfg.config["Laser"]:
                self.laserButton.setStyleSheet("color: green;")
        else:
            self.laserButton.setStyleSheet("color: black;")
        if self.lcfg.config["EShutter"]:
            self.EShutterButton.setStyleSheet("color: green;")
        else:
            self.EShutterButton.setStyleSheet("color: black;")
        if self.lcfg.config["PShutter"]:
            self.PShutterButton.setStyleSheet("color: green;")
        else:
            self.EShutterButton.setStyleSheet("color: black;")
        self.CAREdit.setText(str(self.lcfg.config["Current A"]["Read"]))
        self.CASEdit.setText(str(self.lcfg.config["Current A"]["Set"]))
        self.CBREdit.setText(str(self.lcfg.config["Current B"]["Read"]))
        self.CBSEdit.setText(str(self.lcfg.config["Current B"]["Set"]))
        self.TAREdit.setText(str(self.lcfg.config["Temperature A"]["Read"]))
        self.TASEdit.setText(str(self.lcfg.config["Temperature A"]["Set"]))
        self.TBREdit.setText(str(self.lcfg.config["Temperature B"]["Read"]))
        self.TBSEdit.setText(str(self.lcfg.config["Temperature B"]["Set"]))

        @ignore_connection_error
        @update_config
        @self.update_ui
        def laser_switch(button_status: bool):
            if self.lcfg.config["Laser"]:
                self.remote.apiput("/settings/LSR/0")
                self.lcfg.config["Laser"] = False
            else:
                self.remote.apiput("/settings/LSR/1")
                self.lcfg.config["Laser"] = True
            
        self.laserButton.clicked.connect(laser_switch)

        @ignore_connection_error
        @update_config
        @self.update_ui
        def e_shutter_switch(button_status: bool):
            if self.lcfg.config["EShutter"]:
                self.remote.apiput("/settings/SHU/", value='0')
                self.lcfg.config["EShutter"] = False
            else:
                # self.remote.apiput("/settings/SHU/", value='1')
                self.remote.apiget("/laser_on/")
                self.lcfg.config["EShutter"] = True

        self.EShutterButton.clicked.connect(e_shutter_switch)

        @ignore_connection_error
        @update_config
        @self.update_ui
        def p_shutter_switch(button_status: bool):
            if self.lcfg.config["PShutter"]:
                self.remote.apiput("/settings/TSH/", value='0')
                self.lcfg.config["PShutter"] = False
            else:
                self.remote.apiput("/settings/TSH/", value='1')
                self.lcfg.config["PShutter"] = True

        self.PShutterButton.clicked.connect(p_shutter_switch)

        @ignore_connection_error
        @update_config
        @self.update_ui
        def read_current_A(button_status: bool):
            rc = self.remote.apiget("/settings/CUR/")
            self.lcfg.config["Current A"]["Read"] = rc["CUR"]

        self.CARButton.clicked.connect(read_current_A)

        @ignore_connection_error
        @update_config
        @self.update_ui
        def set_current_A(button_status: bool):
            value_to_set = float(self.CASEdit.text())
            str_to_sent = str(int(value_to_set*10))
            # rc = self.remote.apiput("/settings/CUR/", value=str_to_sent)
            self.remote.apiget(f"/set_current/1/{str_to_sent}")
            rc = self.remote.apiget("/settings/CUS/")
            self.lcfg.config["Current A"]["Set"] = float(rc["CUS"])/10

        self.CASButton.clicked.connect(set_current_A)

        @ignore_connection_error
        @update_config
        @self.update_ui
        def read_current_B(button_status: bool):
            rc = self.remote.apiget("/settings/C2R/")
            self.lcfg.config["Current B"]["Read"] = rc["C2R"]

        self.CBRButton.clicked.connect(read_current_B)

        @ignore_connection_error
        @update_config
        @self.update_ui
        def set_current_B(button_status: bool):
            value_to_set = float(self.CBSEdit.text())
            str_to_sent = str(int(value_to_set*10))
            # rc = self.remote.apiput("/settings/C2R/", value=str_to_sent)
            self.remote.apiget(f"/set_current/1/{str_to_sent}")
            rc = self.remote.apiget("/settings/C2S")
            self.lcfg.config["Current B"]["Set"] = float(rc["C2S"])/10

        self.CBSButton.clicked.connect(set_current_B)

        @ignore_connection_error
        @update_config
        @self.update_ui
        def read_temperature_A(button_status: bool = False):
            rc = self.remote.apiget("/settings/SHA/")
            self.lcfg.config["Temperature A"]["Read"] = rc["SHA"]

        self.TARButton.clicked.connect(read_temperature_A)

        @ignore_connection_error
        @update_config
        @self.update_ui
        def set_temperature_A(button_status: bool = False):
            value_to_set = float(self.CASEdit.text())
            str_to_sent = str(value_to_set*10)
            rc = self.remote.apiput("/settings/SHA/", value=str_to_sent)
            # rc = self.remote.apiget("/SHA")
            self.lcfg.config["Temperature A"]["Set"] = rc["SHA"]

        self.TASButton.clicked.connect(set_temperature_A)

        @ignore_connection_error
        @update_config
        @self.update_ui
        def read_temperature_B(button_status: bool):
            rc = self.remote.apiget("/settings/SHB/")
            self.lcfg.config["Temperature B"]["Read"] = rc["SHB"]

        self.TBRButton.clicked.connect(read_temperature_B)

        @ignore_connection_error
        @update_config
        @self.update_ui
        def set_temperature_B(button_status: bool):
            value_to_set = float(self.CBSEdit.text())
            str_to_sent = str(value_to_set*10)
            rc = self.remote.apiput("/settings/SHB/", value=str_to_sent)
            # rc = self.remote.apiget("/SHB")
            self.lcfg.config["Temperature B"]["Set"] = rc["SHB"]

        self.TBSButton.clicked.connect(set_temperature_B)

    def update_ui(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            func(*args, **kwargs)
            if self.lcfg.config["Laser"]:
                self.laserButton.setStyleSheet("color: green;")
            else:
                self.laserButton.setStyleSheet("color: black;")
            if self.lcfg.config["EShutter"]:
                self.EShutterButton.setStyleSheet("color: green;")
            else:
                self.EShutterButton.setStyleSheet("color: black;")
            if self.lcfg.config["PShutter"]:
                self.PShutterButton.setStyleSheet("color: green;")
            else:
                self.PShutterButton.setStyleSheet("color: black;")
            self.CAREdit.setText(str(self.lcfg.config["Current A"]["Read"]))
            self.CASEdit.setText(str(self.lcfg.config["Current A"]["Set"]))
            self.CBREdit.setText(str(self.lcfg.config["Current B"]["Read"]))
            self.CBSEdit.setText(str(self.lcfg.config["Current B"]["Set"]))
            self.TAREdit.setText(str(self.lcfg.config["Temperature A"]["Read"]))
            self.TASEdit.setText(str(self.lcfg.config["Temperature A"]["Set"]))
            self.TBREdit.setText(str(self.lcfg.config["Temperature B"]["Read"]))
            self.TBSEdit.setText(str(self.lcfg.config["Temperature B"]["Set"]))
        return wrapper


lcfg = LabConfig()
cpa_controller = QApplication(sys.argv)
mainWindow = MainWindow(lcfg= lcfg)
mainWindow.show()
sys.exit(cpa_controller.exec())