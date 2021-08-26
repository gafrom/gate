from scipy.spatial import distance
from collections import deque
import itertools

class Frame:
  def __init__(self, a, b, c, coordinates):
    self.a = a # palm point where a hand connects to an arm
    self.b = b # palm point where finger 2 starts
    self.c = c # palm point where finger 5 starts
    self.coord = coordinates

class GestureRecognizer:
  """docstring for GestureRecognizer"""

  STATES_LIMIT = 10 # how many previous states to keep
  FRAMES_LIMIT = 30 # how many previous frames to keep

  FREE = "_free_"
  PCLUTCH = "Pcltch"
  NCLUTCH = "Ncltch"
  PSLIDE = "Pslide"
  NSLIDE = "Nslide"

  def __init__(self):
    self.state = self.FREE
    self.states = deque([self.state], self.STATES_LIMIT)
    self.frames = deque([], self.FRAMES_LIMIT)

    self.hand = Hand(self.frames)

  def process(self, frame):
    self.frames.append(frame)
    self._update_state()

    self.log();
    # if self.hand.has_positive_velocity() and self.hand.has_negative_velocity():
    #   import pdb;
    #   pdb.set_trace()


    return self.state

  def reset(self):
    self.states.clear()
    self.frames.clear()

  def _update_state(self):
    # FROM FREE
    if self.state == self.FREE:
      if self.hand.is_still():
        if   self.hand.is_nclutch():
          self._set_state(self.NCLUTCH)
        elif self.hand.is_pclutch():
          self._set_state(self.PCLUTCH)

    # FROM NCLUTCH
    elif self.state == self.NCLUTCH:
      if self.hand.is_nclutch():
        if self.hand.is_still() or self.hand.has_positive_velocity():
          return
        elif self.hand.has_negative_velocity():
          self._set_state(self.NSLIDE)

      elif self.hand.is_pclutch():
        self._set_state(self.PCLUTCH)

      else:
        self._free()

    # FROM PCLUTCH
    elif self.state == self.PCLUTCH:
      if self.hand.is_pclutch():
        if self.hand.is_still() or self.hand.has_negative_velocity():
          return
        elif self.hand.has_positive_velocity():
          self._set_state(self.PSLIDE)

      elif self.hand.is_nclutch():
        self._set_state(self.NCLUTCH)

      else:
        self._free()

    # FROM NSLIDE
    elif self.state == self.NSLIDE:
      if self.hand.is_nclutch():
        if self.hand.is_still() or self.hand.has_positive_velocity():
          self._set_state(self.NCLUTCH)
        elif self.hand.has_negative_velocity():
          return
      else:
        self._free()

    # FROM PSLIDE
    elif self.state == self.PSLIDE:
      if self.hand.is_pclutch():
        if self.hand.is_still() or self.hand.has_negative_velocity():
          self._set_state(self.PCLUTCH)
        elif self.hand.has_positive_velocity():
          return
      else:
        self._free()


  def _set_state(self, new_state):
    self.state = new_state
    self.states.append(self.state)

  def _free(self):
    self._set_state(self.FREE) 

  def log(self):
    print(f"state: {self.state}; is_still: {self.hand.is_still()}; " + \
          f"PosC: {self.hand.is_pclutch()}; NegC: {self.hand.is_nclutch()}; " +\
          f"posV: {self.hand.has_positive_velocity()}; negV: {self.hand.has_negative_velocity()}.")


class Hand:
  X_AXIS = 1 # left/right movements
  Y_AXIS = 0 # forward/backward
  Z_AXIS = 2 # up/down movements - the lower the value the higher the point off the ground

  # in HandyCoordinateSystem, distance between points considered the same
  X_ACCURACY = 0.005 # 0.01
  Z_ACCURACY = 0.003

  # in absolute coordinate system, distance between points considered a step
  STEP_DISTANCE = 0.001

  def __init__(self, frames):
    self.frames = frames
    self.finger1 = Finger(1)
    self.finger2 = Finger(2)
    self.finger3 = Finger(3)
    self.finger4 = Finger(4)
    self.finger5 = Finger(5)

    self.eucl_dist = distance.euclidean

  # hand is in positive clutch
  def is_pclutch(self):
    # TODO: check timing for frames
    return all(self._is_open(frame.coord) and self._is_pready(frame) for frame in self._last_frames(2))

  # hand is in negative clutch
  def is_nclutch(self):
    # TODO: check timing for frames
    return all(self._is_open(frame.coord) and self._is_nready(frame) for frame in self._last_frames(2))

  def is_still(self):
    posns = [frame.a for frame in self._last_frames(2)]
    return all(self._same(posns, i) for i in range(0, len(posns) - 1))

  # if moving with positive velocity along X axis
  def has_positive_velocity(self):
    posns = [frame.a for frame in self._last_frames(2)]
    if len(posns) < 2:
      return False
    return all(self._is_positive_delta(posns[i+1], posns[i]) for i in range(0, len(posns) - 1))

  # if moving with negative velocity along X axis
  def has_negative_velocity(self):
    posns = [frame.a for frame in self._last_frames(2)]
    if len(posns) < 2:
      return False
    return all(self._is_positive_delta(posns[i], posns[i+1]) for i in range(0, len(posns) - 1))

  def _is_positive_delta(self, curr_point, prev_point):
    return curr_point[self.X_AXIS] - prev_point[self.X_AXIS] > self.STEP_DISTANCE

  def _same(self, posns, fi):
    return self.eucl_dist(posns[fi], posns[fi + 1]) < self.X_ACCURACY

  def _is_inside(self, point):
    return 1 if point[self.Y_AXIS] < 0.5 else -1

  def _is_open(self, coords):
    return self.finger2.is_open(coords) and \
           self.finger3.is_open(coords) and \
           self.finger4.is_open(coords) and \
           self.finger5.is_open(coords)

  # is ready for positive movement
  def _is_pready(self, frame):
    l, r = self._get_left_right_points(frame)

    # the left point is lower than the right point
    return l[self.Z_AXIS] > r[self.Z_AXIS] + self.Z_ACCURACY

  # is ready for negative movement
  def _is_nready(self, frame):
    l, r = self._get_left_right_points(frame)
    # the right point is lower than the left point
    return r[self.Z_AXIS] > l[self.Z_AXIS] + self.Z_ACCURACY

  def _last_frames(self, n):
    return itertools.islice(reversed(self.frames), 0, n)

  def _get_left_right_points(self, frame):
    return sorted([frame.b, frame.c], key=lambda point: -point[self.X_AXIS]) 

class Finger:
  INDEX = {
    1: 4,
    2: 8,
    3: 12,
    4: 16,
    5: 20
  }
  THRESHOLD_NON_THUMB = 1.8
  THRESHOLD_THUMB = 1.1

  def __init__(self, number):
    self.number = number
    # self.index = self.INDEX[self.number]
    if self.number == 1:
      self.th = self.THRESHOLD_THUMB
      self.axis = 0 # thumb closes along X axis
      self.sign = 1 # means ">"
    else:
      self.th = self.THRESHOLD_NON_THUMB
      self.axis = 1 # non-thumb closes along Y axis
      self.sign = 1 # means ">"

  def is_open(self, coordinates):
    # import pdb; pdb.set_trace()
    # print(coordinates[0])
    return abs(coordinates[self.number - 1][self.axis]) * self.sign > self.th * self.sign
