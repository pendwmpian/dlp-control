# DLP_CONTROL

This repository contains code for controlling Texas Instruments DLPC900(C) evaluation boards.

## Install

```bash
pip install "git+https://github.com/pendwmpian/dlp-control"
```

## Requirements

- Python >= 3.7
- C++ Compiler 
+ __Windows__: MSVC 14.x or later (Visual Studio 2022 is recommended) with the Windows SDK.
+ __Linux__: g++

## How to use

The core functions are provided by the PatternOnTheFly class.

+ `__init__(self, h=1080, w=1920, test=False)`:
    `h`: Height of the DMD in pixels.
    `w`: Width of the DMD in pixels.
    `test`: If True, USB packet transmission is skipped (useful for testing without a connected device).

+ `DefinePattern(self, index, exposure, darktime, data: np.ndarray)`:
    Register a Pattern Image in 1-bit Bitmap format.
    `index`: Order of the image in sequence (0-indexed)
    `exposure`: Pattern exposure time (us)
    `darktime`: Dark display time following the exposure (us)
    `data`: A 2D NumPy array representing the 1-bit bitmap (0 for black, 1 for white).

+ `SendImageSequence(self, nPattern: int, nRepeat: int)`:
    Sends the registered patterns to the DLPC900. This can take a significant amount of time (approximately 1 second to 1 minute / pattern).
    `nPattern`: The total number of patterns in the sequence.
    `nDisplay`: The number of times to repeat the entire sequence. If set to 0, the sequence will loop indefinitely.

+ `StartRunning()`:
    Starts displaying the registered pattern sequence on the DMD.

+ `StopRunning()`:
    Stops displaying the pattern sequences.

## Example

```python
from pattern_on_the_fly import PatternOnTheFly
import numpy as np

def create_lattice_img(size, p):
    """Creates a lattice pattern image."""
    img = np.zeros((size[0], size[1]), dtype=np.uint8)
    for i in range(0, size[0], p):
        for j in range(0, size[1], p):
            # Simplified logic for checkerboard pattern based on blocks
            if ((i // p) + (j // p)) % 2 == 0:
                img[i:min(size[0], i + p), j:min(size[1], j + p)] = 1
    return img

# Initialize the DMD controller (defaults to 1080x1920 resolution)
dmd = PatternOnTheFly()

# Define three lattice patterns with different grid sizes
# Pattern 0: 50x50 pixel grid
dmd.DefinePattern(index=0, exposure=2000000, darktime=0,
                  data=create_lattice_img((1080, 1920), 50))

# Pattern 1: 80x80 pixel grid
dmd.DefinePattern(index=1, exposure=2000000, darktime=0,
                  data=create_lattice_img((1080, 1920), 80))

# Pattern 2: 120x120 pixel grid
dmd.DefinePattern(index=2, exposure=2000000, darktime=0,
                  data=create_lattice_img((1080, 1920), 120))

# Send the sequence of 3 patterns to the DLPC900, repeating 10 times
dmd.SendImageSequence(nPattern=3, nRepeat=10)

# Start displaying the patterns
dmd.StartRunning()

# To stop (if needed, typically after some event or time):
# dmd.StopRunning()
```

