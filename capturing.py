# from picamera.array import PiRGBArray
# from picamera import PiCamera
import time
import cv2
import pdb
from threading import Thread

class Capturing:
  def __init__(self, lock):
    self.lock = lock
    self.latest_image = None
    self.thread = Thread(name="Capturing", target=self._capture, daemon=False)
    self.enabled = True

    # camera = PiCamera()
    # camera.resolution = (640, 480)
    # camera.resolution = (1920, 1080)
    # camera.resolution = (1280, 720)
    # camera.framerate = 16
    # rawCapture = PiRGBArray(camera, size=camera.resolution)

    self.cap = cv2.VideoCapture(0)

  def start(self):
    self.thread.start()

  def stop(self):
    self.enabled = False
    time.sleep(0.3)
    self.cap.release()

  def _capture(self):
    print("Warming up camera ...")
    time.sleep(0.5)

    while self.enabled:
      res, image = self.cap.read()
      if not res:
        print("Error: result is null, aborting video capturing...")
        return stop()

      image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
      image.flags.writeable = False

      with self.lock:
        self.latest_image = image

    self.stop()

  def write_image(self, file_name, image, results):
    multi_hand_landmarks = results.multi_hand_landmarks
    if multi_hand_landmarks:
      for hand_landmarks in multi_hand_landmarks:
        mp_drawing.draw_landmarks(
          image, hand_landmarks, mp_hands.HAND_CONNECTIONS)
    # cv2.imshow('MediaPipe Hands', image)
    cv2.imwrite(file_name, image)

