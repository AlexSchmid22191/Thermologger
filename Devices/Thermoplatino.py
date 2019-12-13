from serial import Serial
from threading import Lock
from time import sleep


class Thermoplatino(Serial):
    def __init__(self, port):
        Serial.__init__(self, port, timeout=1.5, baudrate=115200)
        self.com_lock = Lock()

        sleep(1)

        with self.com_lock:
            self.write(":FUNC 'TEMP'\n".encode())

    def read_temperature(self):
        with self.com_lock:

            self.write(':read?'.encode())
            self.write('\n'.encode())

            answer = self.readline().decode()

            try:
                return float(answer)

            except ValueError:
                return answer
