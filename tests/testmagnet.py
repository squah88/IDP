#magnet sensor test

import magnetsensor
import time

while True:
    reading = magnetsensor.read_magnet()
    print("raw:", magnetsensor.magnet_sensor.read_u16(), " pole:", reading)
    time.sleep(0.5)