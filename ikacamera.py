# coding: utf-8

import time
import picamera
import cv2
import numpy as np
import io
import os
import urllib2
import MultipartPostHandler
from datetime import datetime
from datetime import timedelta

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
    win_coursed_count = 0
    lose_coursed_count = 0

    win_frame_tmp = None
    lose_frame_tmp = None

    wait_time = datetime.now()

    while True:
        camera.capture(stream, format="jpeg", use_video_port=True)
        frame = np.fromstring(stream.getvalue(), dtype=np.uint8)
        stream.seek(0)
        frame = cv2.imdecode(frame, 1)

        image_gray = cv2.cvtColor(frame, cv2.cv.CV_BGR2GRAY)

        win_rects = cascade_win.detectMultiScale(image_gray, scaleFactor=1.1, minNeighbors=1, minSize=(1, 1))
        lose_rects = cascade_lose.detectMultiScale(image_gray, scaleFactor=1.1, minNeighbors=1, minSize=(1, 1))

        if win_coursed_count is 20:
            if win_frame_count >= 5 and wait_time < datetime.now():
                now = datetime.now()
                wait_time = now + timedelta(seconds=10)

                path = save(win_frame_tmp, dist, now.strftime('%Y%m%d%H%M%S'), 'win')
                send(path, now.strftime('%Y-%m-%d %H:%M:%S'), 'win')

            # 検出経過カウントが上限まで達した場合はカウントをゼロに戻す
            win_coursed_count = 0
            win_frame_count = 0
            win_frame_tmp = None

        elif win_coursed_count is not 0:
            # 検出経過カウントが開始されている場合はインクリメントする
            win_coursed_count += 1

        if lose_coursed_count is 20:
            if lose_frame_count >= 5 and wait_time < datetime.now():
                now = datetime.now()
                wait_time = now + timedelta(seconds=10)

                path = save(lose_frame_tmp, dist, now.strftime('%Y%m%d%H%M%S'), 'lose')
                send(path, now.strftime('%Y-%m-%d %H:%M:%S'), 'lose')

            # 検出経過カウントが上限まで達した場合はカウントをゼロに戻す
            lose_coursed_count = 0
            lose_frame_count = 0
            lose_frame_tmp = None

        elif lose_coursed_count is not 0:
            # 検出経過カウントが開始されている場合はインクリメントする
            lose_coursed_count += 1

        if len(win_rects) > 0:
            win_frame_count += 1

            # 検出経過カウントがまだ開始されていない場合はカウントを開始する
            if win_coursed_count is 0:
                win_coursed_count = 1

            if win_frame_tmp is None:
                win_frame_tmp = capture(camera, stream)

            for rect in win_rects:
                cv2.rectangle(frame, tuple(rect[0:2]), tuple(rect[0:2]+rect[2:4]), (255, 255, 255), thickness=2)

        if len(lose_rects) > 0:
            lose_frame_count += 1

            # 検出経過カウントがまだ開始されていない場合はカウントを開始する
            if lose_coursed_count is 0:
                lose_coursed_count = 1

            if lose_frame_tmp is None:
                lose_frame_tmp = capture(camera, stream)

            for rect in lose_rects:
                cv2.rectangle(frame, tuple(rect[0:2]), tuple(rect[0:2]+rect[2:4]), (255, 0, 0), thickness=2)

        cv2.imshow(window_name, frame)

        key = cv2.waitKey(10)
        if key == 27:
            break

def capture(camera, stream):
    camera.resolution = (640, 480)
    camera.capture(stream, format='jpeg')
    frame = np.fromstring(stream.getvalue(), dtype=np.uint8)
    stream.seek(0)
    frame = cv2.imdecode(frame, 1)
    camera.resolution = (160, 120)

    return frame

def save(frame, dist, now, result):
    path = '{0}/ika_result{1}_{2}.jpg'.format(dist, now, result)
    cv2.imwrite(path, frame)

    return path

def send(path, now, result):
    opener = urllib2.build_opener(MultipartPostHandler.MultipartPostHandler)
    params = {'result': result, 'datetime': now, 'secret': 'fe45a06194f2fa0ab43fa5412bd686764ffe2748d614ccf584431716e8111116fe0cb53220d652e6ec311f846f8a52de29e7fd65a97a88ca4b4b2be188755f73', 'image': open(path, 'rb')}
    opener.open('http://ikashot.net/upload', params)

def main():

    if os.path.exists('result') is False:
        os.mkdir('result')

    cascade_win = cv2.CascadeClassifier("./cascade/ika_result_win.xml")
    cascade_lose = cv2.CascadeClassifier("./cascade/ika_result_lose.xml")

    camera = setup()
    detect(camera, cascade_win, cascade_lose)

    cv2.destroyAllWindows()

main()
