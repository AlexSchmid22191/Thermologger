from serial import Serial
from threading import Lock
from time import sleep


class LeyboldCenterThree(Serial):
    def __init__(self, port, *args, **kwargs):
        Serial.__init__(self, port, timeout=1.5, baudrate=9600)
        self.com_lock = Lock()

        sleep(1)

        with self.com_lock:
            self.write('TID\n'.encode())
            self.readline()

    def read_temperature(self):
        with self.com_lock:

            self.write('PR1\n'.encode())
            self.readline()
            self.write('\x05\n'.encode())
            answer = self.readline().decode()

            try:
                return float(answer.split(',')[-1])

            except ValueError:
                return answer
