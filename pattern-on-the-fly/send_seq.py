from usb_comm import DMD

class PatternOnTheFly(DMD):
    def __init__(self):
        self.usb_w(b"\x1b\x1a", b"\x03") # Change to Pattern On-The-Fly mode

    def _PatternDisplayLUT1bit(self, index, exposure, darktime, ImagePatternIndex, BitPosition):
        payload = b""
        payload += index.to_bytes(2, 'little')
        payload += exposure.to_bytes(3, 'little')
        payload += b"\x01"
        payload += darktime.to_bytes(3, 'little')
        payload += b"\x00"
        buf = (BitPosition << 11) + ImagePatternIndex
        payload += buf.to_bytes(2, 'little')
        self.usb_w(b"\x34\x1a", payload)

    def _InitializePatternBMPLoad(self, ImagePatternIndex, ImageSize):
        payload = b""
        payload += ImagePatternIndex.to_bytes(2, 'little')
        payload += ImageSize.to_bytes(4, 'little')
        self.usb_w(b"\x2a\x1a", payload)

    def _PatternDisplayLUTConf(self, nLUT, nDisPlay):
        """
        nLUT: number of patterns (NP)
        nDisplay: number of patterns to display (ND)
        the number of repeats is calc by ND/NP
        """
        payload = b""
        payload += nLUT.to_bytes(2, 'little')
        payload += nDisPlay.to_bytes(4, 'little')
        self.usb_w(b"\x31\x1a", payload)

    def _ImageHeader(self, nBytes, compression, width = 1920, height = 1080, bgColor: bytearray = b"\x00\x00\x00\x00"):
        """
        nBytes: number of bytes in the encoded image data
        compression: raw(0), Run-Length(1), Enhanced run-length(2)
        """
        buf += b"\x53\x70\x6c\x64"
        buf += width.to_bytes(2, 'little')
        buf += height.to_bytes(2, 'little')
        buf += nBytes.to_bytes(4, 'little')
        buf += b"\xff\xff\xff\xff\xff\xff\xff\xff"
        buf += bgColor
        buf += b"\x00"
        buf += compression.to_bytes(1, 'little')
        buf += b"\x01"
        while len(buf) < 48: buf += b"\x00"
        return buf

    def _PatternBMPLoad(self, ImagePatternIndex, header: bytearray, imagedata: bytearray):
        data = header + imagedata
        self._InitializePatternBMPLoad(ImagePatternIndex, len(data))

        seek = 0
        while seek < len(data):
            payload = b""
            size = min(504, len(data) - seek)
            payload += size.to_bytes(2, 'little')
            payload += data[seek : seek + size]
            seek += size
            self.usb_w(b"\x2b\x1a", payload)

    def _PatternImageLoad(self, ImagePatternIndex, compression, imagedata: bytearray, width = 1920, height = 1080, bgColor: bytearray = b"\x00\x00\x00\x00"):
        """
        Combined _ImageHeader and _PatternBMPLoad

        ImagePatternIndex: Index of Image
        compression: no compression(0), RLE(1), Enhanced RLE(2)
        """
        header = self._ImageHeader(self, len(imagedata), compression, width, height, bgColor)
        self._PatternBMPLoad(ImagePatternIndex, header, imagedata)

    def StartRunning(self):
        self.usb_w(b"\x24\x1a", b"\x02")

    def PauseRunning(self):
        self.usb_w(b"\x24\x1a", b"\x01")

    def StopRunning(self):
        self.usb_w(b"\x24\x1a", b"\x00")