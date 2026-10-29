#we need to test the value north and south give for magnet

import magnetsensor
import time

while True:
    reading = magnetsensor.read_magnet()
    print("raw:", magnetsensor.magnet_sensor.read_u16(), " pole:", reading)
    time.sleep(0.5)