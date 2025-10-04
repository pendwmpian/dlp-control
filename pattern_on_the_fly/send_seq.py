from pattern_on_the_fly.usb_comm import DMD
import pattern_on_the_fly.enhanced_rle as enhanced_rle
import numpy as np
import math

class PatternOnTheFly(DMD):
    def __init__(self, h=1080, w=1920, test=False):
        super().__init__(test=test)
        self.usb_w(b"\x1b\x1a", b"\x03")    # Change to Pattern On-The-Fly mode
        self.ImagePattern24bit = np.zeros((18, h, w), dtype=np.uint32)
        self.index_map = [False] * 400      # reset to False

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
        buf = b"\x53\x70\x6c\x64"
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
        header = self._ImageHeader(len(imagedata), compression, width, height, bgColor)
        self._PatternBMPLoad(ImagePatternIndex, header, imagedata)

    def DefinePattern(self, index, exposure, darktime, data: np.ndarray):
        """
        Register Pattern Images in 1-bit Bitmap format

        index: order of the image in sequence
        exposure: Pattern exposure time (us)
        darktime: Dark display time following the exposure (us)
        data: 1-bit BMP data in 2-d array (0: black, 1: white)
        """

        if index >= 400: raise Exception("index must be < 400")
        unique_vals = np.unique(data)
        invalid_vals = unique_vals[~((unique_vals == 0) | (unique_vals == 1))]
        if invalid_vals.size > 0:
            raise ValueError(f"Pattern data (np.ndarray) must contain only 0s and 1s. Found invalid value(s): {list(invalid_vals)}")
        
        ImagePatternIndex = index // 24
        BitPosition = index % 24
        self.ImagePattern24bit[ImagePatternIndex, :, :] += data.astype(np.uint32) * (1 << (2 - BitPosition // 8) * 8 + BitPosition % 8)
        self._PatternDisplayLUT1bit(index, exposure, darktime, ImagePatternIndex, BitPosition)
        self.index_map[index] = True

    def _checkIndex(self, nPattern):
        for i in range(nPattern):
            if self.index_map[i] is False:
                raise Exception('Pattern index ${i} is missing')
        return True
    
    def _EnhanceRLE(self, index):
        array = enhanced_rle.ERLEencode(self.ImagePattern24bit[index, :, :])
        return (array, 2) if (1920 * 1080 * 3 >= len(array)) else (self.ImagePattern24bit[index, :, :].tobytes(), 0)

    def SendImageSequence(self, nPattern: int, nRepeat: int):
        """
        nPattern: number of Patterns
        nDisplay: number of Repeat. If this value is set to 0, the pattern sequences will be displayed indefinitely.
        """
        if nPattern > 400: raise Exception("nPattern must be <= 400")
        self._checkIndex(nPattern)
        self._PatternDisplayLUTConf(nPattern, nPattern * nRepeat)
        for i in reversed(range(math.ceil(nPattern / 24))):
            imagedata, compression = self._EnhanceRLE(i)
            self._PatternImageLoad(i, compression, imagedata)
        self.ImagePattern24bit = np.zeros_like(self.ImagePattern24bit)

    def CalcSizeOfImageSequence(self, nPattern: int):
        """
        (For Debug Use) Calculate the total size (bytes) of ImageSequence
        nPattern: number of Patterns
        """
        total_size = 0
        for i in reversed(range(math.ceil(nPattern / 24))):
            imagedata, _ = self._EnhanceRLE(i)
            total_size += len(imagedata)
        return total_size

    def EnableTrigOut2(self, InvertedTrigger=False, RaisingEdgeTime = 0, FallingEdgeTime = 0):
        """
        Trigger indicates the start of each pattern in the sequence
        (Trigger is High in Non-Inverted, Low in Inverted)
        """
        if RaisingEdgeTime < -20 or RaisingEdgeTime > 10000 or FallingEdgeTime < -20 or FallingEdgeTime > 10000:
            return False
        payload = b""
        if InvertedTrigger is True:
            payload += b"\x01"
        else: payload += b"\x00"
        payload += RaisingEdgeTime.to_bytes(2, 'little')
        payload += FallingEdgeTime.to_bytes(2, 'little')
        self.usb_w(b"\x1e\x1a", payload)

    def EnableTrigIn2(self, InvertedTrigger=False):
        """
        Non-Inverted: Pattern started on rising edge stopped on falling edge
        Inverted: Pattern started on falling edge stopped on rising edge
        """
        payload = b""
        if InvertedTrigger is True:
            payload += b"\x01"
        else: payload += b"\x00"
        self.usb_w(b"\x36\x1a", payload)

    def StartRunning(self):
        self.usb_w(b"\x24\x1a", b"\x02")

    def PauseRunning(self):
        self.usb_w(b"\x24\x1a", b"\x01")

    def StopRunning(self):
        self.usb_w(b"\x24\x1a", b"\x00")