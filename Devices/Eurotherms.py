import minimalmodbus
from threading import Lock


class Eurotherm3216(minimalmodbus.Instrument):
    """Instrument class for Eurotherm 3216 process controller.
    Args:
    * portname (str): port name
    * slaveaddress (int): slave address in the range 1 to 247
    """

    def __init__(self, portname, slaveadress):
        minimalmodbus.BAUDRATE = 9600
        self.com_lock = Lock()
        minimalmodbus.Instrument.__init__(self, portname, slaveadress)
        self.decimal_precision = 0

    def get_decimal_precision(self):
        """Get the decimal precision stored in the instrument"""
        with self.com_lock:
            self.decimal_precision = self.read_register(525, 0)

    def get_oven_temp(self):
        """Return the current temperature of the internal thermocouple"""
        with self.com_lock:
            temp = self.read_register(1, numberOfDecimals=self.decimal_precision)

        return temp

    def set_target_setpoint(self, temperature):
        """Set the tagert setpoint, in degree Celsius"""
        with self.com_lock:
            self.write_register(2, temperature, numberOfDecimals=self.decimal_precision)

    def set_manual_output_power(self, output):
        """Set the power output of the instrument in percent"""
        with self.com_lock:
            self.write_register(3, output, numberOfDecimals=1)

    def get_working_output(self):
        """Return the current power output of the instrument"""
        with self.com_lock:
            output = self.read_register(4, numberOfDecimals=1)

        return output

    def get_working_setpoint(self):
        """Get the current working setpoint of the instrument"""
        with self.com_lock:
            setpoint = self.read_register(5, numberOfDecimals=self.decimal_precision)

        return setpoint

    def set_rate(self, rate):
        """Set the maximum rate of change for the working setpoint i.e. the max heating/cooling rate"""
        with self.com_lock:
            self.write_register(35, rate, numberOfDecimals=1)

    def set_automatic_mode(self):
        """Set controller to automatic mode"""
        with self.com_lock:
            self.write_register(273, 0)

    def set_manual_mode(self):
        """Set controller to manual mode"""
        with self.com_lock:
            self.write_register(273, 1)

    def write_external_target_temperature(self, temperature):
        """Set an external target setpoint tenperature (for complex temperature programs)"""
        with self.com_lock:
            self.write_register(26, temperature, numberOfDecimals=self.decimal_precision)

    def write_external_sensor_temperature(self, temperature):
        """Write temperature control variable from an external sensor to the instrument """
        with self.com_lock:
            self.write_register(203, temperature, numberOfDecimals=self.decimal_precision)

    def enabele_external_sensor_temperature(self):
        """Enable controlling by the external sensor temperature"""
        with self.com_lock:
            self.write_register(1, 1)
