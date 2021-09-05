import time
from threading import Thread


class Switch:
  SLEEP_TIME_IN_SECONDS = 0.01

  def __init__(self, id, turning_on, turning_off):
    self.id          = id
    self.turning_on  = turning_on
    self.turning_off = turning_off

    # the switch is off at the beginning
    self.time_off = time.time()
    self.event = False

    self.thread = Thread(target=self._polling, name=self.id, daemon=True)
    self.thread.start()

  def boost(self, period_in_seconds=0.3):
    self.time_off = time.time() + period_in_seconds

  def _polling(self):
    # TODO: use Condition class to simplify the logic below
    while True:
      if self.time_off > time.time():
        if self.event:
          time.sleep(self.SLEEP_TIME_IN_SECONDS)
        else:
          self.event = True
          self.turning_on()
      else:
        if self.event:
          self.event = False
          self.turning_off()
        else:
          time.sleep(self.SLEEP_TIME_IN_SECONDS)

  def __enter__(self):
    return self

  def __exit__(self, exc_type, exc_val, exc_tb):
    self.time_off = time.time()
    time.sleep(self.SLEEP_TIME_IN_SECONDS * 2)
