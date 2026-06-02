import sys
import time
from functools import wraps

from PyQt6 import QtWidgets
from PyQt6.QtWidgets import QApplication, QWidget, QMainWindow
from ui.channel import Ui_Channel
from ui.mainwindow import Ui_MainWindow

from components.remote import RemoteCPA
from components.labconfig import LabConfig
from components.utils import ignore_connection_error
from components.qutils import ThreadManager


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
        self.thread_manager = ThreadManager() 

        # setup ui
        if self.channel_config["Enabled"]:
                self.channelSwitchButton.setText("Disable")
                self.channelLabel.setStyleSheet("color: green;")
        else:
            self.channelSwitchButton.setText("Enable")
            self.channelLabel.setStyleSheet("color: black;")

        self.delayEdit.setText(str(self.channel_config["Value"]))
        self.delayIntervalEdit.setText(str(self.channel_config["Increment"]))

        # decorate
        self.switch_channel = update_config(self.switch_channel)
        self.switch_channel = ignore_connection_error(self.switch_channel)
        self.channelSwitchButton.clicked.connect(self.on_switch_channel)

        self.set_delay = update_config(self.set_delay)
        self.set_delay = ignore_connection_error(self.set_delay)
        self.delaySetButton.clicked.connect(self.on_set_delay)

        self.delayIntervalEdit.editingFinished.connect(self.set_delay_increment)

        self.delayIncreaseButton.clicked.connect(self.on_increase_delay)
        self.delayDecreaseButton.clicked.connect(self.on_decrease_delay)


    def switch_channel(self, signals=None):
        if self.channel_config["Enabled"]:
            self.remote.apiput(f"/settings/RUN/{self.channel}/", value="1")
            self.channel_config["Enabled"] = False
        else:
            self.remote.apiput(f"/settings/RUN/{self.channel}/", value="0")
            self.channel_config["Enabled"] = True

    def on_switch_channel(self, button_status: bool):
        signals = self.thread_manager.start_task(self.switch_channel)
        signals.finished.connect(lambda: self.update_ui())


    def set_delay(self, signals=None, value=0.0):
        str_to_sent = str(int(value*10)).zfill(7)
        rc = self.remote.apiput(f"/settings/DLY/{self.channel}/", str_to_sent)
        # rc = self.remote.apiget(f"/DLY/{self.channel}/")
        self.channel_config["Value"] = rc["DLY"][ord(self.channel) - ord('A')]

    def on_set_delay(self, button_status: bool):
        value = float(self.delayEdit.text())
        signals = self.thread_manager.start_task(self.set_delay, value=value)
        signals.finished.connect(lambda: self.update_ui())

    def set_delay_increment(self, lineEdit_status=None):
        delay_increment_to_set = float(self.delayIntervalEdit.text())
        self.channel_config["Increment"] = delay_increment_to_set

    def on_increase_delay(self, button_status: bool):
        value = self.channel_config["Value"] + self.channel_config["Increment"]
        signals = self.thread_manager.start_task(self.set_delay, value=value)
        signals.finished.connect(lambda: self.update_ui())

    def on_decrease_delay(self, button_status: bool):
        value = self.channel_config["Value"] - self.channel_config["Increment"]
        signals = self.thread_manager.start_task(self.set_delay, value=value)
        signals.finished.connect(lambda: self.update_ui())


    def update_ui(self, ):
        if self.channel_config["Enabled"]:
            self.channelSwitchButton.setText("Disable")
            self.channelLabel.setStyleSheet("color: green;")
        else:
            self.channelSwitchButton.setText("Enable")
            self.channelLabel.setStyleSheet("color: black;")

        self.delayEdit.setText(str(self.channel_config["Value"]))
        self.delayIntervalEdit.setText(str(self.channel_config["Increment"]))


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, lcfg: LabConfig):
        super().__init__()
        self.setupUi(self)
        self.lcfg = lcfg
        self.remote = RemoteCPA(host=self.lcfg.config["Host"], port=self.lcfg.config["Port"])
        update_config = self.lcfg.update_config
        self.thread_manager = ThreadManager()

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
            self.PShutterButton.setStyleSheet("color: black;")
        self.CAREdit.setText(str(self.lcfg.config["Current A"]["Read"]))
        self.CASEdit.setText(str(self.lcfg.config["Current A"]["Set"]))
        self.CBREdit.setText(str(self.lcfg.config["Current B"]["Read"]))
        self.CBSEdit.setText(str(self.lcfg.config["Current B"]["Set"]))
        self.TAREdit.setText(str(self.lcfg.config["Temperature A"]["Read"]))
        self.TASEdit.setText(str(self.lcfg.config["Temperature A"]["Set"]))
        self.TBREdit.setText(str(self.lcfg.config["Temperature B"]["Read"]))
        self.TBSEdit.setText(str(self.lcfg.config["Temperature B"]["Set"]))

        # decorate
        self.laser_switch = update_config(self.laser_switch)
        self.laser_switch= ignore_connection_error(self.laser_switch)
        self.laserButton.clicked.connect(self.on_laser_switch)

        self.e_shutter_switch = update_config(self.e_shutter_switch)
        self.e_shutter_switch = ignore_connection_error(self.e_shutter_switch)
        self.EShutterButton.clicked.connect(self.on_e_shutter_switch)

        self.p_shutter_switch = update_config(self.p_shutter_switch)
        self.p_shutter_switch = ignore_connection_error(self.p_shutter_switch)
        self.PShutterButton.clicked.connect(self.on_p_shutter_switch)

        self.read_current_A = update_config(self.read_current_A)
        self.read_current_A = ignore_connection_error(self.read_current_A)
        self.CARButton.clicked.connect(self.on_read_current_A)

        self.set_current_A = update_config(self.set_current_A)
        self.set_current_A = ignore_connection_error(self.set_current_A)
        self.CASButton.clicked.connect(self.on_set_current_A)

        self.read_current_B = update_config(self.read_current_B)
        self.read_current_B = ignore_connection_error(self.read_current_B)
        self.CBRButton.clicked.connect(self.on_read_current_B)

        self.set_current_B = update_config(self.set_current_B)
        self.set_current_B = ignore_connection_error(self.set_current_B)
        self.CBSButton.clicked.connect(self.on_set_current_B)

        self.read_temperature_A = update_config(self.read_temperature_A)
        self.read_temperature_A = ignore_connection_error(self.read_temperature_A)
        self.TARButton.clicked.connect(self.on_read_temperature_A)

        self.set_temperature_A = update_config(self.set_temperature_A)
        self.set_temperature_A = ignore_connection_error(self.set_temperature_A)
        self.TASButton.clicked.connect(self.on_set_temperature_A)

        self.read_temperature_B = update_config(self.read_temperature_B)
        self.read_temperature_B = ignore_connection_error(self.read_temperature_B)
        self.TBRButton.clicked.connect(self.on_read_temperature_B)
        
        self.set_temperature_B = update_config(self.set_temperature_B)
        self.set_temperature_B = ignore_connection_error(self.set_temperature_B)
        self.TBSButton.clicked.connect(self.on_set_temperature_B)


    def laser_switch(self, signals=None):
        if self.lcfg.config["Laser"]:
            self.remote.apiput("/settings/232/", value='0')
            self.remote.apiput("/settings/232/", value='1')
            self.lcfg.config["Laser"] = False
        else:
            self.remote.apiput("/settings/LSR/", value='1')
            self.lcfg.config["Laser"] = True

    def on_laser_switch(self, button_status: bool):
        signals = self.thread_manager.start_task(self.laser_switch)
        signals.finished.connect(lambda: self.update_ui())
    

    def e_shutter_switch(self, signals=None):
        if self.lcfg.config["EShutter"]:
            self.remote.apiput("/settings/SHU/", value='0')
            self.lcfg.config["EShutter"] = False
        else:
            current_A = self.lcfg.config["Current A"]["Set"]
            current_B = self.lcfg.config["Current B"]["Set"]
            # first, set current to 0
            self.set_current_A(value=0.0)
            self.set_current_B(value=0.0)
            # then, open E shutter
            self.remote.apiput("/settings/SHU/", value='1')
            self.lcfg.config["EShutter"] = True
            # finally, set current back to original value
            self.set_current_A_safely(value=current_A)
            self.set_current_B_safely(value=current_B)

    def on_e_shutter_switch(self, button_status: bool):
        signals= self.thread_manager.start_task(self.e_shutter_switch)
        signals.finished.connect(lambda: self.update_ui())


    def p_shutter_switch(self, signals=None):
        if self.lcfg.config["PShutter"]:
            self.remote.apiput("/settings/TSH/", value='0')
            self.lcfg.config["PShutter"] = False
        else:
            self.remote.apiput("/settings/TSH/", value='1')
            self.lcfg.config["PShutter"] = True

    def on_p_shutter_switch(self, button_status: bool):
        signals = self.thread_manager.start_task(self.p_shutter_switch)
        signals.finished.connect(lambda: self.update_ui())


    def read_current_A(self, signals=None):
        rc = self.remote.apiget("/settings/CUR/")
        self.lcfg.config["Current A"]["Read"] = float(rc["CUR"])/10

    def on_read_current_A(self, button_status: bool):
        signals = self.thread_manager.start_task(self.read_current_A)
        signals.finished.connect(lambda: self.update_ui())


    def read_current_B(self, signals=None):
        rc = self.remote.apiget("/settings/C2R/")
        self.lcfg.config["Current B"]["Read"] = float(rc["C2R"])/10

    def on_read_current_B(self, button_status: bool):
        signals = self.thread_manager.start_task(self.read_current_B)
        signals.finished.connect(lambda: self.update_ui())


    def set_current_A(self, signals=None, value=0.0):
        str_to_sent = str(int(value*10))
        # rc = self.remote.apiput("/settings/CUR/", value=str_to_sent)
        self.remote.apiput("/settings/CUR/", value=str_to_sent)
        rc = self.remote.apiget("/settings/CUS/")
        self.lcfg.config["Current A"]["Set"] = float(rc["CUS"])/10

    def set_current_A_safely(self, signals=None, value=0.0):
        if not self.lcfg.config["EShutter"]:
            self.set_current_A(value=value)
        else:
            if value <= self.lcfg.config["Current A"]["Set"]:
                self.set_current_A(value=value)
            else:
                self.read_current_A()
                while self.lcfg.config["Current A"]["Read"] < value:
                    # if  self.lcfg.config["Current A"]["Read"] < 9.0:
                    #     self.set_current_A(value=self.lcfg.config["Current A"]["Read"]+0.2)
                    # else:        
                    #     self.set_current_A(value=self.lcfg.config["Current A"]["Read"]+0.1)
                    self.set_current_A(value=self.lcfg.config["Current A"]["Read"]+0.2)
                    time.sleep(3)
                    self.read_current_A()

    def on_set_current_A(self, button_status: bool):
        value = float(self.CASEdit.text())
        signals = self.thread_manager.start_task(self.set_current_A_safely, value=value)
        signals.finished.connect(lambda: self.update_ui())
    

    def set_current_B(self, signals=None, value=0.0):
        str_to_sent = str(int(value*10))
        # rc = self.remote.apiput("/settings/C2R/", value=str_to_sent)
        self.remote.apiput("/settings/C2R/", value=str_to_sent)
        rc = self.remote.apiget("/settings/C2S")
        self.lcfg.config["Current B"]["Set"] = float(rc["C2S"])/10

    def set_current_B_safely(self, signals=None, value=0.0):
        if not self.lcfg.config["EShutter"]:
            self.set_current_B(value=value)
        else:
            if value <= self.lcfg.config["Current B"]["Set"]:
                self.set_current_B(value=value)
            else:
                self.read_current_B()
                while self.lcfg.config["Current B"]["Read"] < value:
                    # if self.lcfg.config["Current B"]["Read"] < 9.0:
                    #     self.set_current_B(value=self.lcfg.config["Current B"]["Read"]+0.2)
                    # else:        
                    #     self.set_current_B(value=self.lcfg.config["Current B"]["Read"]+0.1)
                    self.set_current_B(value=self.lcfg.config["Current B"]["Read"]+0.2)
                    time.sleep(3)
                    self.read_current_B()

    def on_set_current_B(self, button_status: bool):
        value = float(self.CBSEdit.text())
        signals = self.thread_manager.start_task(self.set_current_B_safely, value=value)
        signals.finished.connect(lambda: self.update_ui())


    def read_temperature_A(self, signals=None):
        rc = self.remote.apiget("/settings/SHA/")
        self.lcfg.config["Temperature A"]["Read"] = rc["SHA"]

    def on_read_temperature_A(self, button_status: bool):
        signals = self.thread_manager.start_task(self.read_temperature_A)
        signals.finished.connect(lambda: self.update_ui())
        

    def set_temperature_A(self, signals=None, value=0.0):
        str_to_sent = str(int(value*100)).zfill(4)
        rc = self.remote.apiput("/settings/SHA/", value=str_to_sent)
        # rc = self.remote.apiget("/SHA")
        self.lcfg.config["Temperature A"]["Set"] = float(rc["SHA"])/100

    def on_set_temperature_A(self, button_status: bool):
        value = float(self.TASEdit.text())
        signals = self.thread_manager.start_task(self.set_temperature_A, value=value)
        signals.finished.connect(lambda: self.update_ui())


    def read_temperature_B(self, signals=None):
        rc = self.remote.apiget("/settings/SHB/")
        self.lcfg.config["Temperature B"]["Read"] = rc["SHB"]

    def on_read_temperature_B(self, button_status: bool):
        signals = self.thread_manager.start_task(self.read_temperature_B)
        signals.finished.connect(lambda: self.update_ui())


    def set_temperature_B(self, signals=None, value=0.0):
        str_to_sent = str(int(value*100)).zfill(4)
        rc = self.remote.apiput("/settings/SHB/", value=str_to_sent)
        # rc = self.remote.apiget("/SHB")
        self.lcfg.config["Temperature B"]["Set"] = float(rc["SHB"])/100

    def on_set_temperature_B(self, button_status: bool):
        value = float(self.TBSEdit.text())
        signals = self.thread_manager.start_task(self.set_temperature_B, value=value)
        signals.finished.connect(lambda: self.update_ui())


    def update_ui(self):
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



lcfg = LabConfig()
cpa_controller = QApplication(sys.argv)
mainWindow = MainWindow(lcfg= lcfg)
mainWindow.show()
sys.exit(cpa_controller.exec())