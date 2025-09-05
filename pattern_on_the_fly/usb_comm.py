import usb.core
import usb.util
import time
import sys

class DMD:
    def __init__(self, test=False):
        # In test mode, no usb connection will be established
        self.test = test
        if self.test is False:
            # find our device
            self.dev = usb.core.find(idVendor=0x0451, idProduct=0xc900)

            # was it found?
            if self.dev is None:
                raise ValueError('Device not found')

            if sys.platform == 'linux':
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
            payload += data[max(0,seek):min(seek+64, len(data))]
            seek += 64
            while len(payload) < 64: payload += b"\x00"
            if self.test is False:
                sent_bytes = self.dev.write(0x01, payload, 1000)
            payload = b""
        
        return sent_bytes

    def usb_r(self, command): # not impl yet
        pass
    
    def close(self):
        usb.util.dispose_resources(self.dev)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()