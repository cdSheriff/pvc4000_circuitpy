import time
import struct

from adafruit_bus_device import i2c_device

from busio import I2C


_RAW_DATA_REGISTER = 0xD0
_DEFAULT_I2C_ADDRESS = 0x50


class PVC4000:
    """

    """

    def __init__(self, i2c_bus: I2C, address: int = _DEFAULT_I2C_ADDRESS):
        self.i2c_device = i2c_device.I2CDevice(i2c_bus, address)
        self._buffer = bytearray(6)
        self._crc_buffer = bytearray(2)

    def read_raw_data(self):
        with self.i2c_device as i2c:
            i2c.write(_RAW_DATA_REGISTER)
            time.sleep(0.05)

        with self.i2c_device as i2c:
            i2c.readinto(self._buffer)

        count = struct.unpack('>H', self._buffer[1:3])[0]

        if count <= 10_000:
            return count
        else:
            return 13.5 * (count - 10_000) + 10_000

    def generate_crc(data) -> int:
        crc = CRC8_INIT
        for current_byte in data:
            crc ^= current_byte
            for _ in range(8):
                if crc & 0x80:
                    crc = (crc << 1) ^ CRC8_POLYNOMIAL
                else:
                    crc = (crc << 1)
                crc &= 0xFF  # Ensure crc stays within 8 bits
        return crc
