import usb.core
import usb.util
import time
import sys

class DMD:
    def __init__(self):
        # find our device
        self.dev = usb.core.find(idVendor=0x0451, idProduct=0xc900)

        # was it found?
        if self.dev is None:
            raise ValueError('Device not found')

        if self.dev.is_kernel_driver_active(0):
            try:
                self.dev.detach_kernel_driver(0)
            except usb.core.USBError as e:
                sys.exit("Could not detach kernel driver: %s" % str(e))

        # set the active configuration. With no arguments, the first
        # configuration will be the active one
        self.dev.set_configuration()

    def usb_w(self, command, data):
        """
        command: USB Command, bytearray
        data: bytearray
        """
        if len(data) > 512:
            return False
        payload = b"\x00\x12"
        dat_len = len(data) + 2
        payload += dat_len.to_bytes(2, 'little')
        payload += command

        seek = -6
        sent_bytes = -1

        while seek < len(data):
            payload += data[max(0,seek):min(seek+64, len(data)-1)]
            seek += 64
            while len(payload) < 64: payload += b"\x00"
            sent_bytes = self.dev.write(0x01, payload, 100)
            payload = b""
        
        return sent_bytes

    def usb_r(self, command): # not impl yet
        pass