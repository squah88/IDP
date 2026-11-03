#code for hall effect sensor

from machine import ADC, Pin
import time
import led

#state the thresholds from magnet test, for what south reads and what nroth reads
LOW_THRESHOLD = 38000
HIGH_THRESHOLD = 41000 #TODO: test values

# Change 26 if the sensor output is connected to another ADC pin
magnet_sensor = ADC(Pin(28))

def read_magnet():
    # take one reading from the Hall sensor
    reading = magnet_sensor.read_u16()
    print(reading)

    if reading < LOW_THRESHOLD:
        return "south"

    elif reading > HIGH_THRESHOLD:
        return "north"

    else:
        # Reading is too close to the middle to identify the pole
        return None




