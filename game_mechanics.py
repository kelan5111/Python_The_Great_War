import pygame
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

    @abstractmethod
    def draw(self, screen):
        pass

    @abstractmethod
    def act(self):
        pass

    def kill(self):
        self._alive = False

    def select(self):
        self._select = True

    def deselect(self):
        self._select = False

    def has_selected(self):
        return self._select

    def is_alive(self):
        return self._alive


class Group:
    def __init__(self, screen):
        self.__actors = []
        self.__screen = screen

    def draw(self):
        for actor in self.__actors:
            actor.draw(self.__screen)

    def act(self):
        for actor in self.__actors:
            actor.act()

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
        self.__shape = pygame.Rect(0, 0, 0, 0)
        self.__country = country
        self.__start_pos = None
        self.__pressed = False

    def draw(self, screen):
        if self.__pressed:
            pygame.draw.rect(screen, self.OUTLINE_COLOUR, self.__shape, 3)

    def act(self):
        pass

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

        self.__shape = pygame.Rect(rect_x, rect_y, rect_w, rect_h)

    def end_drag(self, actors):
        if not self.__pressed:
            return

        self.__pressed = False
        self.__select(actors)

        self.__shape = pygame.Rect(0, 0, 0, 0)

    def __select(self, actors):
        for actor in actors:
            if isinstance(actor, npc.Soldier):
                if (actor.has_collided(self.__shape) and
                        actor.get_country() == self.__country):
                    actor.select()
                else:
                    actor.deselect()

    def pressed(self, mouse_pos):
        self.__pressed = True
        self.__start_pos = Coordinate(mouse_pos[0], mouse_pos[1])

    def is_pressed(self):
        return self.__pressed
