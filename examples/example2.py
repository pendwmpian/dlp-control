from pattern_on_the_fly import PatternOnTheFly
import numpy as np
import time

def create_lattice_img(size, p):
    img = np.zeros(size[0] * size[1], dtype=np.uint8).reshape(size[0], size[1])
    for i in range(size[0] // p + 1):
        for j in range(size[1] // p + 1):
            if (i + j) % 2 == 0:
                img[i * p: min(size[0], (i + 1) * p), j * p: min(size[1], (j + 1) * p)] = 1 
    return img

dmd = PatternOnTheFly(test=True)

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