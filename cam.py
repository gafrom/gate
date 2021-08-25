# from picamera.array import PiRGBArray
# from picamera import PiCamera
import time
import cv2
import mediapipe as mp
import math
from google.protobuf.json_format import MessageToDict
import pdb
# import numpy as np
from scipy.spatial import distance

from handy_coordinate_system import HandyCoordinateSystem
from gesture_recognizer import GestureRecognizer, Frame

from switch import Switch
from lib.models.gate import Gate

mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands

# For webcam input:
cap = cv2.VideoCapture(0)

# camera = PiCamera()
# camera.resolution = (640, 480)
# camera.resolution = (1920, 1080)
# camera.resolution = (1280, 720)
# camera.framerate = 16
# rawCapture = PiRGBArray(camera, size=camera.resolution)

print("Warming up camera ...")
time.sleep(0.5)

th = 1.5
th_for_thumb = 1.1
th_for_ok = 0.1

count = 50000
initial_count = count

o = None

print("Go!")

def finger_tips(handy, land):
  return (handy.convert(list(land[i].values())[:2]) for i in  (4, 8, 12, 16, 20))

def coords(handy, land):
  return (handy.convert(list(land[i].values())[:2]) for i in range(len(land)))

def shows_one(handy, land):
  f1, f2, f3, f4, f5 = finger_tips(handy, land)

  if f1[0] < th_for_thumb and f2[1] > th and f3[1] < th and f4[1] < th and f5[1] < th:
    return True

  return False

def shows_two(handy, land):
  f1, f2, f3, f4, f5 = finger_tips(handy, land)

  if f1[0] < th_for_thumb and\
     ((f2[1] > th and f3[1] > th and f4[1] < th and f5[1] < th) or\
      (f2[1] < th and f3[1] > th and f4[1] < th and f5[1] > th) or\
      (f2[1] < th and f3[1] < th and f4[1] > th and f5[1] > th)):
    return True

  return False

def shows_three(handy, land):
  f1, f2, f3, f4, f5 = finger_tips(handy, land)

  if f1[0] < th_for_thumb and\
     ((f2[1] > th and f3[1] > th and f4[1] > th and f5[1] < th) or\
      (f2[1] < th and f3[1] > th and f4[1] > th and f5[1] > th)):
    return True

  return False

def shows_four(handy, land):
  f1, f2, f3, f4, f5 = finger_tips(handy, land)

  if f1[0] < th_for_thumb and f2[1] > th and f3[1] > th and f4[1] > th and f5[1] > th:
    return True

  return False

def is_ok_gesture(handy, land):
  f1, f2, f3, f4, f5 = finger_tips(handy, land)

  d = distance.euclidean(f1, f2)  

  # if d < 0.3 and f3[1] > th and f4[1] > th and f5[1] > th and f1[1] < th_for_ok + f2[1]:
  if d < 0.3 and f3[1] > th and f4[1] > th and f5[1] > th:
    return True

  return False

def write_image(file_name, image, results):
  multi_hand_landmarks = results.multi_hand_landmarks
  if multi_hand_landmarks:
    for hand_landmarks in multi_hand_landmarks:
      mp_drawing.draw_landmarks(
        image, hand_landmarks, mp_hands.HAND_CONNECTIONS)
    # cv2.imshow('MediaPipe Hands', image)
  cv2.imwrite(file_name, image)

gate = Gate(23, 24)

with Switch("GateOpener", gate.keep_opening, gate.cut_off) as gate_opener, Switch("GateCloser", gate.keep_closing, gate.cut_off) as gate_closer, mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.3, static_image_mode=False, min_tracking_confidence=0.6) as hands:

    gesture_recognizer = GestureRecognizer()

    tstart = time.time()
    lstart = time.time()



    # for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
    while True:
      count -= 1

      if count == 0:
        tend = time.time()
        num = initial_count
        print(f'We did {round(num/(tend-tstart), 2)} frames per second on average')
        print(f"********* Finished {num} loops ***********")
    
        # cv2.imwrite('foo.jpg', o)
        break

      lend = time.time()
      # print(f'loop => {round(lend-lstart, 3)} s')
      lstart = time.time()
      start = time.time()
      # image = frame.array
      res, image = cap.read()
      # res = True
      # print(image.shape)
    

      # cv2.imwrite('raw1.jpg', image) 

      if not res:
        print("Error: result is null")
        break
      # Flip the image horizontally for a later selfie-view display, and convert
      # the BGR image to RGB.
      # image = cv2.cvtColor(cv2.flip(image, 1), cv2.COLOR_BGR2RGB) 
      image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
      # image = image[..., ::-1]
      # image = np.fliplr(image.reshape(-1,3)).reshape(image.shape)
      # cv2.imwrite('raw2.jpg', image) 
      # To improve performance, optionally mark the image as not writeable to
      # pass by reference.
      image.flags.writeable = False
      results = hands.process(image)
      end = time.time()

      # print(f'image processing => {round(end - start, 3)}s')

      # Draw the hand annotations on the image.
      # image.flags.writeable = True
      # image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
      landmarks = results.multi_hand_landmarks

      if landmarks:
      # if True:
        # print(results.multi_hand_landmarks)

        hcs = MessageToDict(results.multi_handedness[0])["classification"]
        hc = hcs[0]

        land = MessageToDict(landmarks[0])['landmark']

        a, b, c = ((land[i]['x'], land[i]['y']) for i in (0, 17, 5))
        handy = HandyCoordinateSystem(a, b, c, (640, 480))

        a, b, c = ((land[i]['x'], land[i]['y'], land[i]['z']) for i in (0, 17, 5))

        # print(round(b[1],5), round(c[1], 5))

        frame = Frame(a, b, c, list(finger_tips(handy, land)))
        gesture = gesture_recognizer.process(frame)

        # print(f"Gesture {gesture}")

        # ft5 = [round(v, 3) for v in list(land[20].values())]
        # print(ft5[2])

        if True:
          if len(results.multi_handedness) > 1 or len(hcs) > 1:
            print("Too many resutls")
          elif gesture == GestureRecognizer.NCLUTCH:
            write_image(f"raw/raw{count}.jpg", image, results)
            print("✊ (close)")
          elif gesture == GestureRecognizer.PCLUTCH:
            print("✊ (open)")
            write_image(f"raw/raw{count}.jpg", image, results)
          elif gesture == GestureRecognizer.NSLIDE:
            print("<--- (closing)")
            write_image(f"raw/raw{count}.jpg", image, results)
            gate_closer.boost()
          elif gesture == GestureRecognizer.PSLIDE:
            print("---> (opening)")
            write_image(f"raw/raw{count}.jpg", image, results)
            gate_opener.boost()
          elif is_ok_gesture(handy, land):
            print("👌")
            # o = image
          elif shows_one(handy, land):
            print("1")
          elif shows_two(handy, land):
            print("2")
          elif shows_three(handy, land):
            print("3")
          elif shows_four(handy, land):
            print("4")
          elif hc["label"] == "Right":
            print("🖐")
          elif hc["label"] == "Left":
            print("🤚")
          else:
            raise "Error - no label in handedness"


      else:
        # gesture_recognizer.reset()
        print(".")
  
      # rawCapture.truncate(0)

      # if cv2.waitKey(5) & 0xFF == ord("q"):
      #   break

cap.release()

