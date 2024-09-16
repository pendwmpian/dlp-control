import cv2
import numpy as np
import time 
import screeninfo
import re
import sys


# the DMD screen is expected to be "screen 1"

m = screeninfo.get_monitors()
m = str(m)
scr_w = re.findall(r"width=\d+",m)
scr_h = re.findall(r"height=\d+",m)
scr_w = re.findall(r"\d+",scr_w[1])
scr_h = re.findall(r"\d+",scr_h[1])

scr_w,scr_h = int(scr_w[0]),int(scr_h[0])

w = scr_w
h = scr_h
fps = 60
lat_size = 1

scr_x = re.findall(r"x=\d+",m)
scr_y = re.findall(r"y=\d+",m)

x = int(re.findall(r"\d+",scr_x[1])[0]) - int(re.findall(r"\d+",scr_x[0])[0])
y = int(re.findall(r"\d+",scr_y[1])[0]) - int(re.findall(r"\d+",scr_y[0])[0])


def create_lattice_img(size, p):
    img = np.zeros(size[0] * size[1] * 3, dtype=np.uint8).reshape(size[0], size[1], 3)
    for i in range(size[0] // p + 1):
        for j in range(size[1] // p + 1):
            if (i + j) % 2 == 0:
                img[i * p: min(size[0], (i + 1) * p), j * p: min(size[1], (j + 1) * p), :] = (255, 255, 255) 
    return img


capname = "window"
cv2.namedWindow(capname, cv2.WND_PROP_FULLSCREEN)
cv2.moveWindow(capname, x, y)
cv2.setWindowProperty(capname, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
cv2.imshow(capname, create_lattice_img((h, w), lat_size))
cv2.waitKeyEx(0)