import time

from linesensor import follow_line

while True:
    follow_line()
    time.sleep_ms(20)
