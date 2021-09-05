# from picamera.array import PiRGBArray
# from picamera import PiCamera
import time
from threading import Thread

import cv2
import mediapipe as mp
from google.protobuf.json_format import MessageToDict
import pdb

from handy_coordinate_system import HandyCoordinateSystem
from gesture_recognizer import GestureRecognizer, Frame

from switch import Switch
from lib.models.gate import Gate



class Processing:
  WAIT_FOR_IMAGE = 0.01

  def __init__(self, lock, capturing, count=500):
    # self.mp_drawing = mp.solutions.drawing_utils
    self.mp_hands = mp.solutions.hands
    self.count = count
    self.lock = lock
    self.capturing = capturing

    # operates on pins 23 and 24
    self.gate = Gate(23, 24)
    self.thread = Thread(name="Processing", target=self._process, daemon=False)
    self.enabled = True

    self.gesture_recognizer = GestureRecognizer()

  def start(self):
    self.thread.start()

  def stop(self):
    self.enabled = False
    time.sleep(0.5)

  def _process(self):
    with Switch("GateOpener", self.gate.keep_opening, self.gate.cut_off) as gate_opener, Switch("GateCloser", self.gate.keep_closing, self.gate.cut_off) as gate_closer, self.mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.3, static_image_mode=False, min_tracking_confidence=0.6) as hands:
      print("Go!")
      started_at = time.time()

      while self.enabled:
        self.count += 1

        with self.lock:
          image = self.capturing.latest_image
          self.capturing.latest_image = None

        if image is None:
          print(f"ERROR - no images present in capturing stack. Sleeping {self.WAIT_FOR_IMAGE}")
          time.sleep(self.WAIT_FOR_IMAGE)
          continue

        self._process_image(image, gate_opener, gate_closer, hands)
 
      ended_at = time.time()
      print(f'We did {round(self.count/(ended_at-started_at), 2)} frames per second on average')
      print(f"********* Finished {self.count} loops ***********")

  def _process_image(self, image, gate_opener, gate_closer, hands):
    # Flip the image horizontally for a later selfie-view display, and convert
    # the BGR image to RGB.
    # image = cv2.cvtColor(cv2.flip(image, 1), cv2.COLOR_BGR2RGB) 
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    results = hands.process(image)

    landmarks = results.multi_hand_landmarks

    if not landmarks:
      return print(f". {self.count}")

    # hcs = MessageToDict(results.multi_handedness[0])["classification"]
    # hc = hcs[0]

    land = MessageToDict(landmarks[0])['landmark']

    a, b, c = ((land[i]['x'], land[i]['y']) for i in (0, 17, 5))
    handy = HandyCoordinateSystem(a, b, c, (640, 480))

    a, b, c = ((land[i]['x'], land[i]['y'], land[i]['z']) for i in (0, 17, 5))

    frame = Frame(a, b, c, list(self._finger_tips(handy, land)))
    gesture = gesture_recognizer.process(frame)

    if len(results.multi_handedness) > 1 or len(hcs) > 1:
      print("Too many resutls")
    elif gesture == GestureRecognizer.NCLUTCH:
      print("✊ (close)")
      # write_image(f"raw/raw{count}.jpg", image, results)
    elif gesture == GestureRecognizer.PCLUTCH:
      print("✊ (open)")
      # write_image(f"raw/raw{count}.jpg", image, results)
    elif gesture == GestureRecognizer.NSLIDE:
      print("<--- (closing)")
      # write_image(f"raw/raw{count}.jpg", image, results)
      gate_closer.boost()
    elif gesture == GestureRecognizer.PSLIDE:
      print("---> (opening)")
      # write_image(f"raw/raw{count}.jpg", image, results)
      gate_opener.boost()

  def _finger_tips(handy, land):
    return (handy.convert(list(land[i].values())[:2]) for i in  (4, 8, 12, 16, 20))

  # def coords(handy, land):
  #   return (handy.convert(list(land[i].values())[:2]) for i in range(len(land)))

