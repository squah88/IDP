from machine import Pin, I2C
from libs.VL53L0X.VL53L0X import VL53L0X
from utime import sleep

#set up pins
i2c_bus = I2C(id=0, sda=Pin(8), scl=Pin(9)) # I2C0 on GP8 & GP9
    # print(i2c_bus.scan())  # Get the address (nb 41=0x29, 82=0x52)
    
    
# Setup vl53l0 object
sensor = VL53L0X(i2c_bus)
sensor.set_Vcsel_pulse_period(sensor.vcsel_period_type[0], 18)
sensor.set_Vcsel_pulse_period(sensor.vcsel_period_type[1], 14)

#create a distance reading function
def read_distance():
    # start measuring
    sensor.start()

    try:
        # take one reading in millimetres
        reading = sensor.read()
    finally:
        # stop measuring, even if reading fails
        sensor.stop()

    return reading