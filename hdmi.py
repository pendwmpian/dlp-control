import usb.core
import usb.util
import time

# find our device
dev = usb.core.find(idVendor=0x0451, idProduct=0xc900)

# was it found?
if dev is None:
    raise ValueError('Device not found')

if dev.is_kernel_driver_active(0):
    try:
        dev.detach_kernel_driver(0)
    except usb.core.USBError as e:
        sys.exit("Could not detach kernel driver: %s" % str(e))

# set the active configuration. With no arguments, the first
# configuration will be the active one
dev.set_configuration()

# # get an endpoint instance
# cfg = dev.get_active_configuration()
# intf = cfg[(0,0)]

# ep = usb.util.find_descriptor(
#     intf,
#     # match the first OUT endpoint
#     custom_match = \
#     lambda e: \
#         usb.util.endpoint_direction(e.bEndpointAddress) == \
#         usb.util.ENDPOINT_OUT)

# assert ep is not None

# write the data
# print(ep)
payload = b'\x00\x12\x08\x00\x00\x11\xff\x01\xff\x01\xff\x01'
while len(payload) < 64: payload += b"\x00"
sent_bytes = dev.write(1, payload, 100)
payload = b'\xc0\x11\x02\x00\x00\x11'
while len(payload) < 64: payload += b"\x00"
sent_bytes = dev.write(1, payload, 100)
print(sent_bytes)
ret = dev.read(0x81, 64, 100)
print(bytearray(ret))
time.sleep(0.1)

payload = b'\x00\x12\x03\x00\x01\x1a\x01' #1A01 01
while len(payload) < 64: payload += b"\x00"
sent_bytes = dev.write(1, payload, 100)
# payload = b'\xc0\x11\x02\x00\x01\x1a'
# while len(payload) < 64: payload += b"\x00"
# sent_bytes = dev.write(1, payload, 100)
# ret = dev.read(0x81, 64, 100)
# print(bytearray(ret))
time.sleep(0.1)

payload = b'\x00\x12\x03\x00\x1b\x1a\x00' #1A1B Video Mode
while len(payload) < 64: payload += b"\x00"
sent_bytes = dev.write(1, payload, 100)
# payload = b'\xc0\x11\x02\x00\x1b\x1a'
# while len(payload) < 64: payload += b"\x00"
# sent_bytes = dev.write(1, payload, 100)
# ret = dev.read(0x81, 64, 100)
# print(bytearray(ret))
# time.sleep(0.1)

# payload = b'\x00\x12\x03\x00\x1b\x1a\x02' #1A1B Video Pattern Mode
# while len(payload) < 64: payload += b"\x00"
# sent_bytes = dev.write(1, payload, 100)
# payload = b'\xc0\x11\x02\x00\x1b\x1a'
# while len(payload) < 64: payload += b"\x00"
# sent_bytes = dev.write(1, payload, 100)
# ret = dev.read(0x81, 64, 100)
# print(bytearray(ret))
# time.sleep(0.1)

