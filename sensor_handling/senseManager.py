# Above: clientManager.py
# Below: senseBaro.py, senseSoil.py

# senseManager periodically calls senseBaro and senseSoil every ___ minutes/hours/days, or more often if directed.

# general scheme:
    # power up the sensor module
    # wait however long it needs to startup
    # pull data
    # cut power to the sensor module
    # rinse and repeat
    
# cutting off power to the sensor module when it isn't being polled is to stop power consumption when not needed.