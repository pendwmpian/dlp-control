# DLP_CONTROL

This repository contains code for controlling Texas Instruments DLPC900(C) evaluation boards.

## Install

```bash
pip install "git+https://github.com/pendwmpian/dlp-control"
```

On Windows, the installation sometimes fails because of the directory exceeds the path length limit on Windows. If you fail, try the command below:

```bash
cd ~
mkdir tmpbuild
$env:TMPDIR="tmpbuild"
pip install "git+https://github.com/pendwmpian/dlp-control"
del tmpbuild
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

+ `UpdateExposureTime(self, index, exposure, darktime)`
    Update the exposure time and dark time for the registered pattern.
    Note: After updating, call SendImageSequence() to apply the changes.

+ `CalcSizeOfImageSequence(self, nPattern: int)`:
    Calculate the total size (bytes) of ImageSequence  
    `nPattern`: The total number of patterns in the sequence.  

+ `SendImageSequence(self, nPattern: int, nRepeat: int)`:
    Sends the registered patterns to the DLPC900. This can take a significant amount of time (approximately 1 second to 1 minute / pattern).  
    `nPattern`: The total number of patterns in the sequence.  
    `nDisplay`: The number of times to repeat the entire sequence. If set to 0, the sequence will loop indefinitely.  

+ `ReorderSequence(self, perm, nPattern: int, nRepeat: int)`:
    Reorder the Pattern sequence.

    `perm`: reorder map; perm[i] specifies the original index for the i-th element in the new sequence.
    `nPattern`: number of Patterns (If None, defaults to the length of `perm`.)
    `nRepeat`: number of Repeat. If this value is set to 0, the pattern sequences will be displayed indefinitely.
    
    Notes:
    This function uses absolute mapping. Each value in `perm` always refers 
    to the 'original' sequence, regardless of any previous reordering 
    operations. It does not perform a relative shift from the current state.

+ `StartRunning()`:
    Starts displaying the registered pattern sequence on the DMD.  

+ `StopRunning()`:
    Stops displaying the pattern sequences.  

## Examples

### example.py

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

### example2.py

```python
dmd = PatternOnTheFly()

for i in range(100):
    dmd.DefinePattern(i, 20000, 0, create_lattice_img((1080, 1920), 200 + i * 3))

# Calling SendImageSequence without arguments displays the entire pattern sequence once.
dmd.SendImageSequence()
dmd.StartRunning()

time.sleep(5)

# Start displaying the patterns in reversed order
dmd.ReorderSequence([99 - i for i in range(100)], nRepeat=1)
dmd.StartRunning()

time.sleep(5)

# You can update individual patterns without re-sending the entire sequence.
for i in range(40):
    dmd.DefinePattern(i + 30, 20000, 0, np.ones((1080, 1920)))
# After updating, call SendImageSequence() to apply the changes.
dmd.SendImageSequence()
dmd.StartRunning()

time.sleep(5)

# Exposure time and dark time can be updated without re-sending patterns.
for i in range(100):
    dmd.UpdateExposureTime(i, 80000, 20000)
# After updating, call SendImageSequence() to apply the changes.
# The sequence can be truncated to a shorter length (Example: display stops after the 80th pattern.)
dmd.SendImageSequence(nPattern=80)
dmd.StartRunning()
```

# example_trigger.py

```python
from pattern_on_the_fly import PatternOnTheFly
import numpy as np

dmd = PatternOnTheFly()

# Enable Trigger 1 (1000 ms delay)
dmd.EnableTrigIn1(Delay=1000)

dmd.DefinePattern(0, 2000000, 0, np.ones((1080, 1920)))

dmd.SendImageSequence(nRepeat=2)

dmd.StartRunning()
# Patterns will be displayed 1000 ms after the first hardware trigger is received following StartRunning().
# If nRepeat > 1, the pattern sequence starts upon each trigger, repeating up to nRepeat times.

# Disable Trigger 1 mode
dmd.DisableTrigIn1()
```