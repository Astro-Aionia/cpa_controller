class JB0():
    def __init__(self):
        self.config = {"CUR": 100, "Delay": {"A": {"Value": 100}, "B": {"Value": 100}}}

jb0 = JB0()

class JB1:
    def __init__(self, jb0: JB0):
        self.jb0 = jb0
        self.config = self.jb0.config
        self.channel_list = [None, None]
        for i, key in enumerate(self.config["Delay"].keys()):
            self.channel_list[i] = JB2(jb0=self.jb0, channel=key)
    
    def set_value(self, x):
        self.config["CUR"] = x

class JB2:
    def __init__(self, jb0, channel):
        self.config = jb0.config
        self.cc = self.config["Delay"][channel]

    def set_value(self, x):
        self.cc["Value"] = x

jb1 = JB1(jb0)
print(jb0.config)

jb1.set_value(50)
print(jb0.config)

jb1.channel_list[0].set_value(50)
print(jb0.config)