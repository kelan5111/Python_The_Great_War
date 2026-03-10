import pygame
import json
from abc import ABC, abstractmethod

import npc
from coordinate import Coordinate, Direction


class Actor(ABC):
    def __init__(self, coord, width, height, group):
        self._world_coord = coord
        self._screen_coord = Coordinate(0, 0)
        self._actor_list = group.get_actors()

        self._width = width
        self._height = height
        self._rect = pygame.Rect(coord.get_coord(), (width, height))

        self._alive = True
        self._select = False
        self._hover = False

        if group is not None:
            group.add(self)

    @abstractmethod
    def draw(self, *args):
        pass

    @abstractmethod
    def act(self, *args):
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
        self._actors = []
        self._screen = screen

    def draw(self, camera):
        for actor in self._actors:
            actor.draw(self._screen, camera)

    def act(self, mouse_pos):
        for actor in self._actors:
            actor.act(mouse_pos)

        # Remove any actors who are not alive
        self._check_removal()

    def add(self, actor):
        self._actors.append(actor)

    def find_all(self, obj_type):
        return [actor for actor in self._actors if isinstance(actor, obj_type)]

    def find(self, obj_type):
        for actor in self._actors:
            if isinstance(actor, obj_type):
                return actor

    def _check_removal(self):
        for actor in self._actors:
            if not actor.is_alive():
                self._actors.remove(actor)

    def remove_all(self, o):
        try:
            for actor in self._actors:
                if isinstance(actor, o):
                    self._actors.remove(actor)
        except TypeError:
            print("Not a valid object.")

    def get_actors(self):
        return self._actors


class NPCGroup(Group):
    def __init__(self, screen):
        super().__init__(screen)


class WeaponGroup(Group):
    def __init__(self, screen):
        super().__init__(screen)


class ParticleGroup(Group):
    def __init__(self, screen):
        super().__init__(screen)


class UIGroup(Group):
    def __init__(self, screen):
        super().__init__(screen)


class EnvironmentGroup(Group):
    def __init__(self, screen):
        super().__init__(screen)


class Camera:
    def __init__(self, width, height):
        self._screen_width = width
        self._screen_height = height

        self._coord = Coordinate(0, 0)
        self._camera_speed = 200

    def update(self, direction, dt):
        new_x = self._coord.get_x()
        new_y = self._coord.get_y()

        new_x += direction.value[0] * (self._camera_speed * dt)
        new_y += direction.value[1] * (self._camera_speed * dt)

        self._coord.set_x(new_x)
        self._coord.set_y(new_y)

    def translate_rect(self, world_rect):
        offset_x = self._coord.get_x()
        offset_y = self._coord.get_y()

        screen_rect = world_rect.copy()

        screen_rect.x = world_rect.x - offset_x
        screen_rect.y = world_rect.y - offset_y

        return screen_rect

    def translate_mouse_pos(self, world_mouse_pos):
        offset_x = self._coord.get_x()
        offset_y = self._coord.get_y()

        screen_mouse_x = world_mouse_pos[0] + offset_x
        screen_mouse_y = world_mouse_pos[1] + offset_y

        return screen_mouse_x, screen_mouse_y

    def translate_coord(self, coord):
        offset_x = self._coord.get_x()
        offset_y = self._coord.get_y()

        screen_coord_x = coord[0] - offset_x
        screen_coord_y = coord[1] - offset_y

        return screen_coord_x, screen_coord_y

    def get_coord(self):
        return self._coord


class Timer:
    def __init__(self):
        self._start_time = 0

        self.start()

    def __str__(self):
        return f"Timer: {self._start_time}"

    def start(self):
        self._start_time = pygame.time.get_ticks()

    def _elapsed(self):
        return pygame.time.get_ticks() - self._start_time

    def is_finished(self, length_secs):
        return self._elapsed() >= length_secs * 1000

    def reset(self):
        self._start_time = pygame.time.get_ticks()
