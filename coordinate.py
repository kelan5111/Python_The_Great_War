import math
from enum import Enum


class Coordinate:
    RADIUS = 150

    def __init__(self, x, y):
        self._x = x
        self._y = y
        self._coord = (x, y)

    def __repr__(self):
        return f'Coordinate: ({self._x}, {self._y})'

    def execute_radius_check(self, other):
        other_x = other.get_x()
        other_y = other.get_y()

        distance_squared = (self._x - other_x) ** 2 + (self._y - other_y) ** 2

        return math.sqrt(distance_squared) < Coordinate.RADIUS

    def calculate_distance(self, other):
        if type(other) != Coordinate:
            other_x = other[0]
            other_y = other[1]
        else:
            other_x = other.get_x()
            other_y = other.get_y()

        distance = math.sqrt(((other_x - self._x) ** 2) + ((other_y - self._y) ** 2))

        return distance

    def get_x(self):
        return self._x

    def set_x(self, x):
        self._x = x

    def get_y(self):
        return self._y

    def set_y(self, y):
        self._y = y

    def get_center(self, width, height):
        return self._x + width / 2, self._y + height / 2

    def equals(self, other):
        if isinstance(other, Coordinate):
            return self._coord != other.get_coord()

    def get_coord(self):
        return self._coord

    def set_coord(self, x, y):
        self._x = x
        self._y = y


class Direction(Enum):
    DEFAULT = (0, 0)
    UP = (0, 1)
    DOWN = (0, -1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)