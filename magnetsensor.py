#code for hall effect sensor
#south = bottom rack, north = top rack
from machine import ADC, Pin

#thresholds for determining north/south pole
low_threshold = 38000       #below this = south pole
high_threshold = 41000      #above this = north pole

magnet_sensor = ADC(Pin(28))

def read_magnet():
    #take one reading
    reading = magnet_sensor.read_u16()

    if reading < low_threshold:
        return "south"

    elif reading > high_threshold:
        return "north"

    else:
        #no magnet identified or too far to tell
        return None