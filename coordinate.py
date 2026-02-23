import math
from enum import Enum


class Coordinate:
    RADIUS = 150

    def __init__(self, x, y):
        self.__x = x
        self.__y = y
        self.__coord = (x, y)

    def __repr__(self):
        return f'Coordinate: ({self.__x}, {self.__y})'

    def execute_radius_check(self, other):
        other_x = other.get_x()
        other_y = other.get_y()

        distance_squared = (self.__x - other_x) ** 2 + (self.__y - other_y) ** 2

        return math.sqrt(distance_squared) < Coordinate.RADIUS

    def calculate_distance(self, other):
        if type(other) != Coordinate:
            other_x = other[0]
            other_y = other[1]
        else:
            other_x = other.get_x()
            other_y = other.get_y()

        distance = math.sqrt(((other_x - self.__x) ** 2) + ((other_y - self.__y) ** 2))

        return distance

    def get_x(self):
        return self.__x

    def set_x(self, x):
        self.__x = x

    def get_y(self):
        return self.__y

    def set_y(self, y):
        self.__y = y

    def calc_center(self, width, height):
        return self.__x + width / 2, self.__y + height / 2

    def get_coord(self):
        return self.__coord

    def set_coord(self, x, y):
        self.__x = x
        self.__y = y


class Direction(Enum):
    UP = (0, 1)
    DOWN = (0, -1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)