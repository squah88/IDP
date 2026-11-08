#distance sensor test
#prints the distance in mm every 0.3 s

import distancesensor
import time

while True:
    print("distance:", distancesensor.read_distance(), "mm")
    time.sleep(0.3)