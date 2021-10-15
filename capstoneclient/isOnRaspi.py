import os

def isOnRaspi ():
    return os.path.exists("/sys/firmware/devicetree/base/model")
