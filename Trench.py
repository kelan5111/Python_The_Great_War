from abc import ABC, abstractmethod
import pygame

from game_mechanics import Actor
from npc import Soldier
from waypoint import Graph


class Trench(Actor, ABC):
    def __init__(self, width, height, total_capacity, coord, country, ground_colour, actors):
        super().__init__(width, coord, height)
        self._coord = coord
        self._width = 50
        self._height = height

        self._outline_colour = (207, 185, 151)
        self._ground_colour = ground_colour
        self._rect = pygame.Rect(coord.get_coord(), (self._width, height))
        self._boarder_rect = pygame.Rect(coord.get_coord(), (self._width, height))

        self._trench_waypoints = Graph(self._width, height, 20)
        self._build_waypoints()
        self._trench_waypoints.debug_game()

        self._total_capacity = total_capacity
        self._country = country
        self._curr_soldiers = []
        self._actors = actors

    def draw(self, screen):
        # Draw the outline of the trench
        pygame.draw.line(screen, self._outline_colour, self._rect.bottomleft, self._rect.topleft, 5)
        pygame.draw.line(screen, self._outline_colour, self._rect.bottomright, self._rect.topright, 5)
        # Drawing the trench's ground
        pygame.draw.rect(screen, self._ground_colour, self._rect)

        self._trench_waypoints.draw(screen)

    def act(self):
        self._update_curr_soldiers()

    def _build_waypoints(self):
        coord_width = self._rect.topleft[0], self._rect.topright[0]
        coord_height = self._rect.topleft[1], self._rect.bottomleft[1]

        self._trench_waypoints.build(coord_width, coord_height)

    def _update_curr_soldiers(self):
        for actor in self._actors:
            if isinstance(actor, Soldier):
                if self._rect.colliderect(actor.get_rect()):
                    self._curr_soldiers.append(actor)

    def get_width(self):
        return self._width

    def get_height(self):
        return self._height


class FrontLineTrench(Trench, ABC):
    def __init__(self, width, height, total_capacity, coord, country, ground_colour, actors):
        super().__init__(width, height, total_capacity, coord, country, ground_colour, actors)


class SupportTrench(Trench, ABC):
    def __init__(self, width, height, total_capacity, coord, country, ground_colour, actors):
        super().__init__(width, height, total_capacity, coord, country, ground_colour, actors)
