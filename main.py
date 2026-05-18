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
            with open("ui_parameters.json") as f:
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

        @ignore_connection_error
        @update_config
        @self.update_ui
        def switch_channel(button_status: bool):
            if self.channel_config["Enalbed"]:
                self.remote.apiput(f"/RUN/{self.channel}/", "1")
                self.channel_config["Enalbed"] = False
            else:
                self.remote.apiput(f"/RUN/{self.channel}/", "0")
                self.channel_config["Enalbed"] = True

        self.channelSwitchButton.clicked.connect(switch_channel)

        @ignore_connection_error
        @update_config
        @self.update_ui
        def set_delay(button_status: bool):
            delay_to_set = float(self.delayEdit.text())
            str_to_sent = str(delay_to_set*10).zfill(7)
            self.remote.apiput(f"/DLY/{self.channel}/Delay/", str_to_sent)
            rc = self.remote.apiget(f"/DLY/{self.channel}/Delay/")
            self.channel_config["Value"] = rc["DLY"]

        self.delaySetButton.clicked.connect(set_delay)

        @self.update_ui
        def set_delay_increment(lineEdit_status):
            delay_increment_to_set = float(self.delayIntervalEdit.text())
            self.channel_config["Increment"] = delay_increment_to_set

        self.delayIntervalEdit.editingFinished.connect(set_delay_increment)

        @ignore_connection_error
        @update_config
        @self.update_ui
        def delay_increase(button_status: bool):
            delay_to_set = self.channel_config["Value"] + self.channel_config["Increment"]
            str_to_sent = str(delay_to_set*10).zfill(7)
            self.remote.apiput(f"/DLY/{self.channel}/Delay/", str_to_sent)
            rc = self.remote.apiget(f"/DLY/{self.channel}/Delay/")
            self.channel_config["Value"] = rc["DLY"]

        self.delayIncreaseButton.clicked.connect(delay_increase)

        @ignore_connection_error
        @update_config
        @self.update_ui
        def delay_decrease(button_status: bool):
            delay_to_set = self.channel_config["Value"] - self.channel_config["Increment"]
            str_to_sent = str(delay_to_set*10).zfill(7)
            self.remote.apiput(f"/DLY/{self.channel}/Delay/", str_to_sent)
            rc = self.remote.apiget(f"/DLY/{self.channel}/Delay/")
            self.channel_config["Value"] = rc["DLY"]
            
        self.delayDecreaseButton.clicked.connect(delay_decrease)

    def update_ui(self, func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            func(*args, **kwargs)
            if self.channel_config["Enalbed"]:
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

        @ignore_connection_error
        @update_config
        @self.update_ui
        def laser_switch(button_status: bool):
            if self.lcfg.config["Laser"]:
                self.remote.apiput("/LSR/0")
                self.lcfg.config["Laser"] = False
            else:
                self.remote.apiput("/LSR/1")
                self.lcfg.config["Laser"] = True
            
        self.laserButton.clicked.connect(laser_switch)

        @ignore_connection_error
        @update_config
        @self.update_ui
        def e_shutter_switch(button_status: bool):
            if self.lcfg.config["EShutter"]:
                self.remote.apiput("/SHU/0")
                self.lcfg.config["EShutter"] = False
            else:
                self.remote.apiput("/SHU/1")
                self.lcfg.config["EShutter"] = True

        self.EShutterButton.clicked.connect(e_shutter_switch)

        @ignore_connection_error
        @update_config
        @self.update_ui
        def p_shutter_switch(button_status: bool):
            if self.lcfg.config["PShutter"]:
                self.remote.apiput("/THS/0")
                self.lcfg.config["PShutter"] = False
            else:
                self.remote.apiput("/THS/1")
                self.lcfg.config["PShutter"] = True

        self.PShutterButton.clicked.connect(p_shutter_switch)

        @ignore_connection_error
        @update_config
        @self.update_ui
        def read_current_A(button_status: bool):
            rc = self.remote.apiget("/CUR/")
            self.lcfg.config["Current A"]["Read"] = rc["CUR"]

        self.CARButton.clicked.connect(read_current_A)

        @ignore_connection_error
        @update_config
        @self.update_ui
        def set_current_A(button_status: bool):
            value_to_set = float(self.CASEdit.text())
            str_to_sent = str(int(value_to_set*10))
            self.remote.apiput("/CUR/", value=str_to_sent)
            rc = self.remote.apiget("/CUS")
            self.lcfg.config["Current A"]["Set"] = rc["CUS"]

        self.CARButton.clicked.connect(set_current_A)

        @ignore_connection_error
        @update_config
        @self.update_ui
        def read_current_B(button_status: bool):
            rc = self.remote.apiget("/C2R/")
            self.lcfg.config["Current B"]["Read"] = rc["C2R"]

        self.CBRButton.clicked.connect(read_current_B)

        @ignore_connection_error
        @update_config
        @self.update_ui
        def set_current_B(button_status: bool):
            value_to_set = float(self.CBSEdit.text())
            str_to_sent = str(int(value_to_set*10))
            self.remote.apiput("/C2R/", value=str_to_sent)
            rc = self.remote.apiget("/C2S")
            self.lcfg.config["Current A"]["Set"] = rc["C2S"]

        self.CBRButton.clicked.connect(set_current_B)

        @ignore_connection_error
        @update_config
        @self.update_ui
        def read_temperature_A(button_status: bool = False):
            rc = self.remote.apiget("/SHA/")
            self.lcfg.config["Temperature A"]["Read"] = rc["SHA"]

        self.TARButton.clicked.connect(read_temperature_A)

        @ignore_connection_error
        @update_config
        @self.update_ui
        def set_temperature_A(button_status: bool = False):
            value_to_set = float(self.CASEdit.text())
            str_to_sent = str(value_to_set*10)
            self.remote.apiput("/SHA/", value=str_to_sent)
            rc = self.remote.apiget("/SHA")
            self.lcfg.config["Temperature A"]["Set"] = rc["SHA"]

        self.TARButton.clicked.connect(set_temperature_A)

        @ignore_connection_error
        @update_config
        @self.update_ui
        def read_temperature_B(button_status: bool):
            rc = self.remote.apiget("/SHB/")
            self.lcfg.config["Temperature B"]["Read"] = rc["SHB"]

        self.TBRButton.clicked.connect(read_temperature_B)

        @ignore_connection_error
        @update_config
        @self.update_ui
        def set_temperature_B(button_status: bool):
            value_to_set = float(self.CBSEdit.text())
            str_to_sent = str(value_to_set*10)
            self.remote.apiput("/SHB/", value=str_to_sent)
            rc = self.remote.apiget("/SHB")
            self.lcfg.config["Temperature A"]["Set"] = rc["SHB"]

        self.TBRButton.clicked.connect(set_temperature_B)

    def update_ui(self, func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            func(*args, **kwargs)
            if self.lcfg.config["Laser"]:
                self.laserButton.setStyleSheet("color: green;")
            else:
                self.laserButton.setStyleSheet("color: black;")
            if self.lcfg.config["EShutter"]:
                self.EShutterButton.setStyleSheet("color: green;")
            else:
                self.shutterButton.setStyleSheet("color: black;")
            if self.lcfg.config["PShutter"]:
                self.PShutterButton.setStyleSheet("color: green;")
            else:
                self.shutterButton.setStyleSheet("color: black;")
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