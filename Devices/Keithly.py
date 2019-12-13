from serial import Serial
from threading import Lock
from time import sleep


class Keithly(Serial):
    def __init__(self, port):
        Serial.__init__(self, port, timeout=1.5)
        self.com_lock = Lock()

        sleep(1)

        with self.com_lock:
            self.write(":FUNC 'TEMP'\n".encode())

    def read_temperature(self):
        print('test')
        with self.com_lock:
            self.write(':read?'.encode())
            self.write('\n'.encode())

            return float(self.read(16).decode())
