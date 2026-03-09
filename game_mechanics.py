import pygame
import json
from abc import ABC, abstractmethod

import npc
from coordinate import Coordinate, Direction


class Actor(ABC):
    def __init__(self, coord, width, height):
        self._world_coord = coord
        self._screen_coord = Coordinate(0, 0)

        self._width = width
        self._height = height
        self._rect = pygame.Rect(coord.get_coord(), (width, height))

        self._alive = True
        self._select = False
        self._hover = False

    @abstractmethod
    def draw(self, screen, camera):
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
        return self._world_coord

    def get_width(self):
        return self._width

    def get_height(self):
        return self._height

    def set_diameters(self, width, height):
        self._width = width
        self._height = height
        self._rect = pygame.Rect(self._world_coord.get_coord(), (width, height))

    def get_x(self):
        return self._world_coord.get_x()

    def get_y(self):
        return self._world_coord.get_y()

    def get_centre(self):
        return self._world_coord.calc_center(self._width, self._height)

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

    def get_rect(self):
        return self._rect


class Group:
    def __init__(self, screen):
        self.__actors = []
        self.__screen = screen

    def draw(self, camera):
        for actor in self.__actors:
            actor.draw(self.__screen, camera)

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


class Camera:
    def __init__(self, width, height):
        self.__screen_width = width
        self.__screen_height = height

        self.__coord = Coordinate(0, 0)
        self.__camera_speed = 200

    def update(self, direction, dt):
        new_x = self.__coord.get_x()
        new_y = self.__coord.get_y()

        new_x += direction.value[0] * (self.__camera_speed * dt)
        new_y += direction.value[1] * (self.__camera_speed * dt)

        self.__coord.set_x(new_x)
        self.__coord.set_y(new_y)

    def translate_rect(self, world_rect):
        offset_x = self.__coord.get_x()
        offset_y = self.__coord.get_y()

        screen_rect = world_rect.copy()

        screen_rect.x = world_rect.x - offset_x
        screen_rect.y = world_rect.y - offset_y

        return screen_rect

    def translate_mouse_pos(self, world_mouse_pos):
        offset_x = self.__coord.get_x()
        offset_y = self.__coord.get_y()

        screen_mouse_x = world_mouse_pos[0] + offset_x
        screen_mouse_y = world_mouse_pos[1] + offset_y

        return screen_mouse_x, screen_mouse_y

    def translate_coord(self, coord):
        offset_x = self.__coord.get_x()
        offset_y = self.__coord.get_y()

        screen_coord_x = coord[0] - offset_x
        screen_coord_y = coord[1] - offset_y

        return screen_coord_x, screen_coord_y

    def get_coord(self):
        return self.__coord


class Timer:
    def __init__(self):
        self.__start_time = None

    def start(self):
        self.__start_time = pygame.time.get_ticks()

    def __elapsed(self):
        return pygame.time.get_ticks() - self.__start_time

    def finished(self, length_secs):
        return self.__elapsed() >= length_secs * 1000
