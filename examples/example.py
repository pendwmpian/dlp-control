from pattern_on_the_fly import PatternOnTheFly
import numpy as np

def create_lattice_img(size, p):
    img = np.zeros(size[0] * size[1], dtype=np.uint8).reshape(size[0], size[1])
    for i in range(size[0] // p + 1):
        for j in range(size[1] // p + 1):
            if (i + j) % 2 == 0:
                img[i * p: min(size[0], (i + 1) * p), j * p: min(size[1], (j + 1) * p)] = 1 
    return img

dmd = PatternOnTheFly(test=True)

dmd.DefinePattern(0, 2000000, 0, create_lattice_img((1080, 1920), 50))
dmd.DefinePattern(1, 2000000, 0, create_lattice_img((1080, 1920), 80))
dmd.DefinePattern(2, 2000000, 0, create_lattice_img((1080, 1920), 120))
dmd.SendImageSequence(3, 10)
dmd.StartRunning()