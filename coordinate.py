import math


class Coordinate:
    RADIUS = 5

    def __init__(self, x, y):
        self.__x = x
        self.__y = y
        self.__coord = (x, y)

    def __repr__(self):
        return f'Coordinate: ({self.__x}, {self.__y})'

    def execute_radius_check(self, other):
        other_x = other.get_x()
        other_y = other.get_y()

        if ((self.__x - other_x) ** 2 + (self.__y - other_y) ** 2) < Coordinate.RADIUS ** 2:
            return True

        return False

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

    def get_y(self):
        return self.__y

    def get_coord(self):
        return self.__coord

    def set_coord(self, x, y):
        self.__x = x
        self.__y = y
