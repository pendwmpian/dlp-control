import cv2
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

scr_x = re.findall(r"x=\d+",m)
scr_y = re.findall(r"y=\d+",m)

x = int(re.findall(r"\d+",scr_x[1])[0]) - int(re.findall(r"\d+",scr_x[0])[0])
y = int(re.findall(r"\d+",scr_y[1])[0]) - int(re.findall(r"\d+",scr_y[0])[0])


result = cv2.imread("./La Promenade, la femme à l'ombrelle.jpg")
result = cv2.rotate(result, cv2.ROTATE_90_CLOCKWISE)
height, width, ch = result.shape
rgb_cv2_image = cv2.resize(result, dsize=(int(h/height*width),scr_h))

capname = "window"
cv2.namedWindow(capname, cv2.WND_PROP_FULLSCREEN)
cv2.moveWindow(capname, x, y)
cv2.setWindowProperty(capname, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
cv2.imshow(capname, rgb_cv2_image)
cv2.waitKeyEx(0)