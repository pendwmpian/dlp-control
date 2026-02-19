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
        self.exposures = [0] * 400
        self.darktimes = [0] * 400
        self.updatedPattern24bit = [False] * 9
        self.firstPatterninPrevOrder = 0
        self.SetTriggerOnFirstPattern = False
        self.DMD_height = h; self.DMD_width = w

    def _PatternDisplayLUT1bit(self, index, exposure, darktime, ImagePatternIndex, BitPosition, TriggerRequirement=False):
        payload = b""
        payload += index.to_bytes(2, 'little')
        payload += exposure.to_bytes(3, 'little')
        payload += b"\x01" if TriggerRequirement is False else b"\x81"
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

    def DefinePattern(self, index, exposure, darktime, data: np.ndarray, TrigIn1Requirement=False):
        """
        Register Pattern Images in 1-bit Bitmap format

        index: order of the image in sequence
        exposure: Pattern exposure time (us)
        darktime: Dark display time following the exposure (us)
        data: 1-bit BMP data in 2-d array (0: black, 1: white)
        TrigIn1Requirement: Set the Trigger In 1 requirement for the initation of the pattern (the setting is overwritten by EnableTrigIn1() when the index is 0)
        """

        if index >= 400: raise Exception("index must be < 400")
        unique_vals = np.unique(data)
        invalid_vals = unique_vals[~((unique_vals == 0) | (unique_vals == 1))]
        if invalid_vals.size > 0:
            raise ValueError(f"Pattern data (np.ndarray) must contain only 0s and 1s. Found invalid value(s): {list(invalid_vals)}")
        
        if index == 0 and self.SetTriggerOnFirstPattern is True:
            TrigIn1Requirement = True  # Force Overwrite

        ImagePatternIndex = index // 24
        BitPosition = index % 24
        ImagePatternMask = ~(np.ones(shape=(self.DMD_height, self.DMD_width), dtype=np.uint32) * (1 << (2 - BitPosition // 8) * 8 + BitPosition % 8))
        self.ImagePattern24bit[ImagePatternIndex, :, :] &= ImagePatternMask
        self.ImagePattern24bit[ImagePatternIndex, :, :] += data.astype(np.uint32) * (1 << (2 - BitPosition // 8) * 8 + BitPosition % 8)
        # When updating 24-bit images, especially odd-indexed ones, 
        # the preceding 24-bit image likely needs to be updated afterward as well.
        self.updatedPattern24bit[ImagePatternIndex // 2] = True 

        self._PatternDisplayLUT1bit(index, exposure, darktime, ImagePatternIndex, BitPosition, TriggerRequirement=TrigIn1Requirement)
        self.index_map[index] = True
        self.exposures[index] = exposure
        self.darktimes[index] = darktime

    def _checkIndex(self, nPattern):
        for i in range(nPattern):
            if self.index_map[i] is False:
                raise Exception('Pattern index ' + str(i) + ' is missing')
        return True
    
    def _EnhanceRLE(self, index):
        array = enhanced_rle.ERLEencode(self.ImagePattern24bit[index, :, :])
        return (array, 2) if (1920 * 1080 * 3 >= len(array)) else (self.ImagePattern24bit[index, :, :].tobytes(), 0)

    def SendImageSequence(self, nPattern: int = None, nRepeat: int = 1):
        """
        nPattern: number of Patterns (If None, defaults to the maximum registered frame.)
        nRepeat:  number of Repeat. If this value is set to 0, the pattern sequences will be displayed indefinitely.
        """
        if nPattern is None: nPattern = max([0] + [i + 1 for i,e in enumerate(self.index_map) if e is True])
        elif nPattern > 400: raise Exception("nPattern must be <= 400")
        if nPattern <= 0: raise Exception("nPattern must be > 0")
        self._checkIndex(nPattern)
        self._PatternDisplayLUTConf(nPattern, nPattern * nRepeat)
        for i in reversed(range(math.ceil(nPattern / 24))):
            if self.updatedPattern24bit[i // 2] is False: continue
            imagedata, compression = self._EnhanceRLE(i)
            self._PatternImageLoad(i, compression, imagedata)
        self.updatedPattern24bit = [False] * 9

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
    
    def ReorderSequence(self, perm, nPattern: int = None, nRepeat: int = 1, TrigIn1Requirement=False):
        """
        Reorder the Pattern sequence

        perm: reorder map; perm[i] specifies the original index for the i-th element in the new sequence.
        nPattern: number of Patterns (If None, defaults to the length of `perm`.)
        nRepeat:  number of Repeat. If this value is set to 0, the pattern sequences will be displayed indefinitely.
        TrigIn1Requirement: Set the Trigger In 1 requirement for the initation of the pattern (the setting is overwritten by EnableTrigIn1() when the index is 0)
        
        Notes:
        This function uses absolute mapping. Each value in `perm` always refers 
        to the 'original' sequence, regardless of any previous reordering 
        operations. It does not perform a relative shift from the current state.
        """

        if nPattern is None: nPattern = len(perm)
        elif nPattern > 400: raise Exception("nPattern must be <= 400")
        if nPattern <= 0: raise Exception("nPattern must be > 0")

        for old_idx in perm:
            if old_idx >= 400 or self.index_map[old_idx] is False: raise Exception("index " + str(old_idx) + " is missing.")

        if self.SetTriggerOnFirstPattern is True:
            TrigIn1Requirement = True  # Force Overwrite

        if TrigIn1Requirement:
            self._PatternDisplayLUT1bit(self.firstPatterninPrevOrder, self.exposures[self.firstPatterninPrevOrder], self.darktimes[self.firstPatterninPrevOrder], self.firstPatterninPrevOrder // 24, self.firstPatterninPrevOrder % 24, TriggerRequirement=False)
            self._PatternDisplayLUT1bit(perm[0], self.exposures[perm[0]], self.darktimes[perm[0]], perm[0] // 24, perm[0] % 24, TriggerRequirement=True)

        self.firstPatterninPrevOrder = perm[0]

        nDisPlay = nPattern * nRepeat

        self._PatternDisplayLUTConf(nPattern, nDisPlay)

        payload = b""
        payload += nPattern.to_bytes(2, 'little')
        payload += nDisPlay.to_bytes(4, 'little')
        for new, old in enumerate(perm):
            payload += old.to_bytes(2, 'little')
        self.usb_w(b"\x32\x1a", payload)

    def EnableTrigOut2(self, InvertedTrigger=False, RaisingEdgeTime = 0, FallingEdgeTime = 0):
        """
        Trigger indicates the start of each pattern in the sequence
        (Trigger is High in Non-Inverted, Low in Inverted)
        The Default Pulse Width is 20 us. 
        Pulse Width = FallingEdgeTime - RaisingEdgeTime + 20 (us)

        RaisingEdgeTime: Trigger output Raising Edge delay (us) (-20 ~ 20000)
        FallingEdgeTime: Trigger output Falling Edge delay (us) (-20 ~ 20000)
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

    def EnableTrigIn1(self, Delay=105, InvertedTrigger=False, SetTriggerOnFirstPattern=True):
        """
        Delay: Trigger In 1 delay (us)
        Non-Inverted: Pattern started on rising edge stopped on falling edge
        Inverted: Pattern started on falling edge stopped on rising edge
        SetTriggerOnFirstPattern: Set the trigger 1 requirement on the first pattern of the sequence
        """
        if SetTriggerOnFirstPattern is True:
            self.SetTriggerOnFirstPattern = True
        payload = b""
        payload += Delay.to_bytes(2, 'little')
        if InvertedTrigger is True:
            payload += b"\x01"
        else: payload += b"\x00"
        self.usb_w(b"\x35\x1a", payload)

    def DisableTrigIn1(self):
        self.SetTriggerOnFirstPattern = False

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