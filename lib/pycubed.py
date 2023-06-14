import digitalio
import board
import busio
import time
import neopixel
import sdcardio
import sys
import storage
import microcontroller
import analogio
import pycubed_rfm9x_fsk
import configuration.radio_configuration as rf_config


class device:
    """
    Based on the code from: https://docs.python.org/3/howto/descriptor.html#properties
    Attempts to return the appropriate hardware device.
    If this fails, it will attempt to reinitialize the hardware.
    If this fails again, it will raise an exception.
    """

    def __init__(self, fget=None):
        self.fget = fget
        self._device = None

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        if self.fget is None:
            raise AttributeError(f'unreadable attribute {self._name}')

        if self._device is not None:
            return self._device
        else:
            self._device = self.fget(instance)
            return self._device


class _Satellite:

    def __init__(self):
        """ Big init routine as the whole board is brought up. """
        self.BOOTTIME = int(time.monotonic())  # get monotonic time at initialization
        self.micro = microcontroller
        self.micro.on_next_reset(self.micro.RunMode.NORMAL)  # make sure it always resets in normal mode
        self._vbatt = analogio.AnalogIn(board.BATTERY)  # Battery voltage

        # To force initialization of hardware
        self.spi
        self.sdcard
        self.vfs
        self.neopixel
        self.radio

    @device
    def spi(self):
        try:
            return busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
        except Exception as e:
            print("[ERROR][Initializing SPI]", e)

    @device
    def sdcard(self):
        """ Define SD Parameters and initialize SD Card """
        try:
            return sdcardio.SDCard(self.spi, board.SD_CS, baudrate=4000000)
        except Exception as e:
            print('[ERROR][Initializing SD Card]', e)

    @device
    def vfs(self):
        try:
            vfs = storage.VfsFat(self.sdcard)
            storage.mount(vfs, "/sd")
            sys.path.append("/sd")
            return vfs
        except Exception as e:
            print('[ERROR][Initializing VFS]', e)

    @device
    def neopixel(self):
        """ Define neopixel parameters and initialize """
        try:
            led = neopixel.NeoPixel(
                board.NEOPIXEL, 1, brightness=0.2, pixel_order=neopixel.GRB)
            led[0] = (0, 0, 0)
            return led
        except Exception as e:
            print('[ERROR][Initializing Neopixel]', e)

    @device
    def radio(self):
        """ Define radio parameters and initialize UHF radio """
        try:
            self._rf_cs = digitalio.DigitalInOut(board.RF_CS)
            self._rf_rst = digitalio.DigitalInOut(board.RF_RST)
            self.radio_DIO0 = digitalio.DigitalInOut(board.RF_IO0)
            self.radio_DIO0.switch_to_input()
            self.radio_DIO1 = digitalio.DigitalInOut(board.RF_IO1)
            self.radio_DIO1.switch_to_input()
            self._rf_cs.switch_to_output(value=True)
            self._rf_rst.switch_to_output(value=True)
        except Exception as e:
            print('[ERROR][Initializing Radio]', e)

        try:
            radio = pycubed_rfm9x_fsk.RFM9x(
                self.spi,
                self._rf_cs,
                self._rf_rst,
                rf_config.FREQUENCY,
                checksum=rf_config.CHECKSUM)

            radio.dio0 = self.radio_DIO0

            radio.tx_power = rf_config.TX_POWER
            radio.bitrate = rf_config.BITRATE
            radio.frequency_deviation = rf_config.FREQUENCY_DEVIATION
            radio.rx_bandwidth = rf_config.RX_BANDWIDTH
            radio.preamble_length = rf_config.PREAMBLE_LENGTH
            radio.ack_delay = rf_config.ACK_DELAY
            radio.ack_wait = rf_config.ACK_WAIT
            radio.ack_retries = rf_config.ACK_RETRIES
            radio.receive_timeout = rf_config.RECEIVE_TIMEOUT
            radio.node = rf_config.SATELLITE_ID
            radio.destination = rf_config.GROUNDSTATION_ID

            radio.sleep()
            return radio
        except Exception as e:
            print('[ERROR][Initializing RADIO]', e)


cubesat = _Satellite()
