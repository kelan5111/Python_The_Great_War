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

        self._alive = True
        self._select = False
        self._hover = False

    @abstractmethod
    def draw(self, screen):
        pass

    @abstractmethod
    def act(self, mouse_pos):
        pass

    def get_coord(self):
        return self._coord

    def get_width(self):
        return self._width

    def get_height(self):
        return self._height

    def get_x(self):
        return self._coord.get_x()

    def get_y(self):
        return self._coord.get_y()

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

    def __remove(self):
        for actor in self.__actors:
            if not actor.is_alive():
                self.__actors.remove(actor)

    def get_actors(self):
        return self.__actors


class SelectBox(Actor, ABC):
    OUTLINE_COLOUR = (0, 0, 0)

    def __init__(self, country, coord=None, width=None, height=None):
        super().__init__(coord, width, height)
        self.__rect = pygame.Rect(0, 0, 0, 0)
        self.__country = country
        self.__start_pos = None
        self.__pressed = False

    def draw(self, screen):
        if self.__pressed:
            pygame.draw.rect(screen, self.OUTLINE_COLOUR, self.__rect, 3)

    def act(self, mouse_pos):
        self.execute(mouse_pos)

    def execute(self, mouse_pos):
        if not self.__pressed:
            return

        self.__update(mouse_pos)
        # self.__select(soldiers)

    def __update(self, mouse_pos):
        start_x, start_y = self.__start_pos.get_x(), self.__start_pos.get_y()
        current_x, current_y = mouse_pos[0], mouse_pos[1]

        rect_x = min(start_x, current_x)
        rect_y = min(start_y, current_y)
        rect_w = abs(start_x - current_x)
        rect_h = abs(start_y - current_y)

        self.__rect = pygame.Rect(rect_x, rect_y, rect_w, rect_h)

    def end_drag(self, actors):
        if not self.__pressed:
            return

        self.__pressed = False
        self.__select(actors)

        self.__rect = pygame.Rect(0, 0, 0, 0)

    def __select(self, actors):
        for actor in actors:
            if isinstance(actor, npc.Soldier):
                if (self.has_collided(actor) and
                        actor.get_country() == self.__country):
                    actor.set_select(True)
                else:
                    actor.set_select(False)

    def has_collided(self, other):
        if isinstance(other, tuple):
            return self.__rect.collidepoint(other)
        elif isinstance(other, npc.Soldier):
            soldier_rect = other.get_rect()
            return self.__rect.colliderect(soldier_rect)

    def pressed(self, mouse_pos):
        self.__pressed = True
        self.__start_pos = Coordinate(mouse_pos[0], mouse_pos[1])

    def is_pressed(self):
        return self.__pressed


class JSONLoader:
    def __init__(self, file_path):
        self.file_path = file_path
        self.__data = self.__load_data()

    def __load_data(self):
        with open(self.file_path) as file:
            return json.load(file)

    def find(self, key_one, key_two):
        if key_one not in self.__data:
            return None

        for item in self.__data[key_one]:  # list under trenchOne
            if key_two in item:
                return item[key_two][0]  # first frontLine object

        return None

    def __extract(self):
        pass
