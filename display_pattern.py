import cv2
import numpy as np
import tqdm
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

scr_x = re.findall(r"x=\d+",m)
scr_y = re.findall(r"y=\d+",m)

x = int(re.findall(r"\d+",scr_x[1])[0]) - int(re.findall(r"\d+",scr_x[0])[0])
y = int(re.findall(r"\d+",scr_y[1])[0]) - int(re.findall(r"\d+",scr_y[0])[0])


def create_monochromatic_img(size):
    r = 255 * np.random.randint(0, 2, (size[0], size[1], 1), dtype=np.uint8)
    g = 255 * np.random.randint(0, 2, (size[0], size[1], 1), dtype=np.uint8)
    b = 255 * np.random.randint(0, 2, (size[0], size[1], 1), dtype=np.uint8)
    return np.concatenate([r, r, r], axis=2)


capname = "window"
cv2.namedWindow(capname, cv2.WND_PROP_FULLSCREEN)
cv2.moveWindow(capname, x, y)
cv2.setWindowProperty(capname, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
for _ in tqdm.tqdm(range(fps * 100)): # create random patterns
    cv2.imshow(capname, create_monochromatic_img((h, w)))
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
#cv2.waitKeyEx(0)