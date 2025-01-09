import time
import struct

from typing import Union, Tuple

from adafruit_bus_device import i2c_device

from busio import I2C

_CALIBRATED_DATA_REGISTER = 0x00
_RAW_DATA_REGISTER = 0xD0
_DEFAULT_I2C_ADDRESS = 0x50


class PVC4000:
    """
    Class implementing Posifa PVC4000 i2c commands

    Quickstart:
    #################################################
    # follow common Adafruit i2c sensor flow, i.e.:
    import time
    import board
    import busio
    import pvc4000

    i2c = busio.I2C(board.SCL, board.SDA)  # initialize i2c bus with standard setup (pins and freq)

    pvc = PVC4000(i2c, address: int = 0x50)  # initialize the sensor with i2c bus (address is optional)

    while True:
        pressure = pvc.pressure  # retrieve pressure data from sensor using the pressure property
        print("PVC4000 reports %d microns Hg" % pressure)  # print retrieved pressure to STDOUT
        time.sleep(2)  # sleep a bit, so we don't get data barf
    #################################################

    Source:
    https://posifatech.com/wp-content/uploads/2020/11/PVC-I2C-Application-Note-v0.9.7.pdf
    https://posifatech.com/wp-content/uploads/2020/11/Datasheet_PVC4000EVK_Vacuum_RevA_C0.6.pdf

    Current status:
    read raw data and read calibrated data only

    Future work:
    read other registers (calibration settings, etc)
    write registers (calibration is the important one)
    """

    def __init__(self, i2c_bus: I2C, address: int = _DEFAULT_I2C_ADDRESS):
        self.i2c_device = i2c_device.I2CDevice(i2c_bus, address)
        self._buffer = bytearray(6)
        self._crc_buffer = bytearray(2)

    def read_raw_data(self) -> Union[Tuple[None, None], Tuple[int, int]]:
        """

        :return: tuple of pressure (microns mercury), temperature (C)
        """
        with self.i2c_device as i2c:
            i2c.write(_RAW_DATA_REGISTER)
            time.sleep(0.05)

        with self.i2c_device as i2c:
            i2c.readinto(self._buffer)

        if PVC4000.check_sum(self._buffer[0], self._buffer[1:6]) is True:
            pass
        else:
            print('Invalid raw data! yikes!')
            print('bytearray dump: ', self._buffer)
            return None, None

        count = struct.unpack('>H', self._buffer[1:3])[0]
        temp = struct.unpack('>HH', self._buffer[1:3])[0]

        if count <= 10_000:
            return count, temp
        else:
            return 13.5 * (count - 10_000) + 10_000, temp

    # def read_calibrated_data(self) -> Union[None, int]:
    #     """
    #
    #     :return: pressure (microns mercury)
    #     """
    #     with self.i2c_device as i2c:
    #         i2c.write(_CALIBRATED_DATA_REGISTER)
    #         time.sleep(0.05)
    #
    #     with self.i2c_device as i2c:
    #         i2c.readinto(self._buffer)
    #
    #     if PVC4000.check_sum(self._buffer[0], self[1:5]):
    #         pass
    #     else:
    #         print('Invalid calibrated data! Yikes!')
    #         print('bytearray dump: ', self._buffer)
    #         return None
    #
    #     count = struct.unpack('>H', self._buffer[1:3])[0]
    #
    #     if count <= 10_000:
    #         return count
    #     else:
    #         return 13.5 * (count - 10_000) + 10_000

    @property
    def pressure(self) -> Union[None, int]:
        """

        :return: pressure (microns mercury)
        """

        with self.i2c_device as i2c:
            i2c.write(_CALIBRATED_DATA_REGISTER)
            time.sleep(0.05)

        with self.i2c_device as i2c:
            i2c.readinto(self._buffer)

        if PVC4000.check_sum(self._buffer[0], self[1:5]):
            pass
        else:
            print('Invalid calibrated data! Yikes!')
            print('bytearray dump: ', self._buffer)
            return None

        count = struct.unpack('>H', self._buffer[1:3])[0]

        if count <= 10_000:
            return count
        else:
            return 13.5 * (count - 10_000) + 10_000

    @staticmethod
    def check_sum(csum: int, data: bytearray) -> bool:
        """
        Posifa method to verify data payload
        pass in "crc" byte (checksum) and data bytes, get a bool of the data veracity

        :param csum: checksum provided in data payload
        :param data: data payload (without checksum)
        :return: boolean result of checksum
        """

        # negative of the sum of data bytes, 8 bit modulo, twos complimented, plus one
        # should equal the checksum provided in data payload
        return (-(sum(data) % 256) + 0xff) + 0x01 == csum
