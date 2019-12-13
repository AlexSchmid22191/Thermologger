from serial import Serial
from threading import Lock


class Pyrometer(Serial):
    def __init__(self, port):
        Serial.__init__(self, port, timeout=1.5)
        self.com_lock = Lock()

    def read_temperature(self):
        with self.com_lock:
            self.write('TEMP'.encode())
            self.write('\r'.encode())

            answer = self.read_until(b'\r', 20).decode()
            temp = float(answer.split()[0])
            return temp
