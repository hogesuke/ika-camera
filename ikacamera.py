# coding: utf-8

import time
import picamera
import cv2
import numpy as np
import io
import os
from datetime import datetime

def setup():
    camera = picamera.PiCamera()
    camera.resolution = (160, 120)
    camera.framerate = 60

    camera.start_preview()
    time.sleep(2)

    return camera

def detect(camera, cascade_win, cascade_lose):
    window_name = 'image'
    cv2.namedWindow(window_name)

    dist = 'result/pictures_' + datetime.now().strftime('%Y%m%d')
    if os.path.exists(dist) is False:
        os.mkdir(dist)

    stream = io.BytesIO()

    win_frame_count = 0
    lose_frame_count = 0

    while True:
        camera.capture(stream, format="jpeg", use_video_port=True)
        frame = np.fromstring(stream.getvalue(), dtype=np.uint8)
        stream.seek(0)
        frame = cv2.imdecode(frame, 1)

        image_gray = cv2.cvtColor(frame, cv2.cv.CV_BGR2GRAY)

        win_rects = cascade_win.detectMultiScale(image_gray, scaleFactor=1.1, minNeighbors=1, minSize=(1, 1))
        lose_rects = cascade_lose.detectMultiScale(image_gray, scaleFactor=1.1, minNeighbors=1, minSize=(1, 1))

        if len(win_rects) > 0:
            win_frame_count += 1

            for rect in win_rects:
                cv2.rectangle(frame, tuple(rect[0:2]), tuple(rect[0:2]+rect[2:4]), (255, 255, 255), thickness=2)

            if win_frame_count > 3:
                win_frame_count = 0
                capture(camera, dist, 'win')
        else:
            win_frame_count = 0

        if len(lose_rects) > 0:
            lose_frame_count += 1

            for rect in lose_rects:
                cv2.rectangle(frame, tuple(rect[0:2]), tuple(rect[0:2]+rect[2:4]), (255, 0, 0), thickness=2)

            if lose_frame_count > 3:
                lose_frame_count = 0
                capture(camera, dist, 'lose')
        else:
            lose_frame_count = 0

        cv2.imshow(window_name, frame)

        key = cv2.waitKey(10)
        if key == 27:
            break

def capture(camera, dist, result):
    now = datetime.now().strftime('%Y%m%d%H%M%S')
    camera.resolution = (640, 480)
    camera.capture('{0}/ika_result{1}_{2}.jpg'.format(dist, now, result))
    camera.resolution = (160, 120)

def main():

    if os.path.exists('result') is False:
        os.mkdir('result')

    cascade_win = cv2.CascadeClassifier("./cascade/ika_result_win.xml")
    cascade_lose = cv2.CascadeClassifier("./cascade/ika_result_lose.xml")

    camera = setup()
    detect(camera, cascade_win, cascade_lose)

    cv2.destroyAllWindows()

main()
