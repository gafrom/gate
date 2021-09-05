import time

from capturing import Capturing
from processing import Processing
from threading import Lock

lock = Lock()

try:
  cap = Capturing(lock=lock)
  proc = Processing(capturing=cap, lock=lock, count=500)

  cap.start()
  proc.start()

  cap.thread.join()
  proc.thread.join()
except BaseException:
  try:
    print("First, terminating the processing...")
    proc.stop()
  except NameError:
    print("Processing was not initialized")

  try:
    print("Next, turning off the capturing...")
    cap.stop()
  except NameError:
    print("Capturing was not initialized")

  print("Allowing 1 second for other threads to finish.")
  time.sleep(1)


