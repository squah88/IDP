#code for hall effect sensor

from machine import ADC, Pin
import time
import led

#state the thresholds from magnet test, for what south reads and what nroth reads
LOW_THRESHOLD = 30000
HIGH_THRESHOLD = 35000 #TODO: test values

# Change 26 if the sensor output is connected to another ADC pin
magnet_sensor = ADC(Pin(26))

def read_magnet():
    # take one reading from the Hall sensor
    reading = magnet_sensor.read_u16()

    if reading < LOW_THRESHOLD:
        return "north"

    elif reading > HIGH_THRESHOLD:
        return "south"

    else:
        # Reading is too close to the middle to identify the pole
        return None


