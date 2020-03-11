from serial import Serial
from time import sleep

ley = Serial(port='/dev/ttyUSB0', timeout=1)

while True:
    ley.write('PR1\n'.encode())
    answer = ley.readline()
    ley.write('\x05\n'.encode())
    answer = ley.readline().decode()
    print(float(answer.split(',')[-1]))
    sleep(0.5)
