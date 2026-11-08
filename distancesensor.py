#distance sensor (VL53L0X time-of-flight) measures how far away the thing in front of it is in mm
#used to check if a rack slot already has a package in it before we drop our package off
#needs VL53L0X.py saved on the pico

from machine import Pin, SoftI2C
from VL53L0X import VL53L0X
import time

#give the sensor a moment to power up before talking to it
time.sleep_ms(500)

#sensor talks to the pico over I2C: SDA (data) on GP16, SCL (clock) on GP17
i2c_bus = SoftI2C(sda=Pin(16), scl=Pin(17), freq=10000)

#set up the sensor
sensor = VL53L0X(i2c_bus)
sensor.set_Vcsel_pulse_period(sensor.vcsel_period_type[0], 18)
sensor.set_Vcsel_pulse_period(sensor.vcsel_period_type[1], 14)

#how many readings to take each time - we use the middle one to avoid a bad reading
readingcount = 3

def read_distance():
    #returns the distance in mm (the middle of the 3 readings), or None if the sensor didn't answer
    readings = []
    for i in range(readingcount):
        #if the sensor doesn't answer, skip that reading instead of crashing the whole robot
        try:
            readings.append(sensor.read())
        except Exception:
            pass

    #no successful readings
    if len(readings) == 0:
        return None

    #sort the readings and return the middle one
    readings.sort()
    return readings[len(readings) // 2]