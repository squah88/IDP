#code for hall effect sensor

from machine import ADC, Pin
import time
import led

#state the thresholds from magnet test, for what south reads and what north reads
low_threshold = 30000
high_threshold = 35000 #TODO: test values

#pin
magnet_sensor = ADC(Pin(26))

def read_magnet():
    #take one reading from the hall sensor
    reading = magnet_sensor.read_u16()

    if reading < low_threshold:
        return "north"

    elif reading > high_threshold:
        return "south"

    else:
        # Reading is too close to the middle to identify the pole
        return None
