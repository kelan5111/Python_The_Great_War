import pygame
import json
from abc import ABC, abstractmethod

import npc
from coordinate import Coordinate


class Actor(ABC):
    def __init__(self, coord, width, height):
        self._coord = coord
        self._width = width
        self._height = height
        self._rect = pygame.Rect(coord.get_coord(), (width, height))

        self._alive = True
        self._select = False
        self._hover = False

    @abstractmethod
    def draw(self, screen):
        pass

    @abstractmethod
    def act(self, mouse_pos):
        pass

    def has_collided(self, other):
        if isinstance(other, tuple):
            return self._rect.collidepoint(other)
        elif isinstance(other, npc.Soldier):
            soldier_rect = other.get_rect()
            return self._rect.colliderect(soldier_rect)

    def get_coord(self):
        return self._coord

    def get_width(self):
        return self._width

    def get_height(self):
        return self._height

    def set_diameters(self, width, height):
        self._width = width
        self._height = height
        self._rect = pygame.Rect(self._coord.get_coord(), (width, height))

    def get_x(self):
        return self._coord.get_x()

    def get_y(self):
        return self._coord.get_y()

    def set_coord(self, x, y):
        self._coord = Coordinate(x, y)

    def get_centre(self):
        return self._coord.calc_center(self._width, self._height)

    def kill(self):
        self._alive = False

    def set_select(self, select):
        self._select = select

    def has_selected(self):
        return self._select

    def has_hover(self):
        return self._hover

    def set_hover(self, hover):
        self._hover = hover

    def is_alive(self):
        return self._alive

    def get_coord(self):
        return self._coord

    def get_rect(self):
        return self._rect


class Group:
    def __init__(self, screen):
        self.__actors = []
        self.__screen = screen

    def draw(self):
        for actor in self.__actors:
            actor.draw(self.__screen)

    def act(self, mouse_pos):
        for actor in self.__actors:
            actor.act(mouse_pos)

        # Remove any actors who are not alive
        self.__remove()

    def add(self, actor):
        self.__actors.append(actor)

    def find(self, obj_type):
        return [actor for actor in self.__actors if isinstance(actor, obj_type)]

    def __remove(self):
        for actor in self.__actors:
            if not actor.is_alive():
                self.__actors.remove(actor)

    def get_actors(self):
        return self.__actors


class Timer:
    def __init__(self):
        self.__start_time = None

    def start(self):
        self.__start_time = pygame.time.get_ticks()

    def __elapsed(self):
        return pygame.time.get_ticks() - self.__start_time

    def finished(self, length_secs):
        return self.__elapsed() >= length_secs * 1000
