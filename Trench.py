from abc import ABC, abstractmethod
import pygame


class Trench:
    COLOUR = (51, 25, 0)

    def __init__(self, width, height, capacity, coord, country):
        self._coord = coord
        self._width = width
        self._height = height
        self._shape = pygame.Rect(coord.get_coord(), (width, height))

        self._capacity = capacity
        self._country = country

    def draw(self, screen):
        pygame.draw.rect(screen, Trench.COLOUR, self._shape)

    def update(self):
        pass

    def calc_trench_size(self):
        pass


class FrontLineTrench(Trench):
    def __init__(self, width, height, capacity, coord, country):
        super().__init__(width, height, capacity, coord, country)


class SupportTrench(Trench):
    def __init__(self, width, height, capacity, coord, country):
        super().__init__(width, height, capacity, coord, country)
