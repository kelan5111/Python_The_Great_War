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

        self._waypoint_graph = Graph(self._width, height, 20)
        self._build_waypoints()
        self._waypoint_graph.debug()

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

        self._waypoint_graph.draw(screen)

    def act(self, mouse_pos):
        self._update_curr_soldiers()
        self._update_rect()

        self._hover = self._rect.collidepoint(mouse_pos)

        self._check_hover()

    def _update_rect(self):
        self._rect = pygame.Rect(self._coord.get_coord(), (self._width, self._height))
        self._boarder_rect = pygame.Rect(self._coord.get_coord(), (self._width, self._height))

    def _build_waypoints(self):
        coord_width = self._rect.topleft[0] - 10, self._rect.topright[0]
        coord_height = self._rect.topleft[1], self._rect.bottomleft[1]

        self._waypoint_graph.build(coord_width, coord_height)
        print([node.get_neighbours() for node in self._waypoint_graph.get_nodes()])

    def _update_curr_soldiers(self):
        for actor in self._actors:
            if self.has_collided(actor) and self.has_selected():
                if actor not in self._curr_soldiers:
                    self._curr_soldiers.append(actor)

    def has_collided(self, other):
        if isinstance(other, tuple):
            return self._rect.collidepoint(other)
        elif isinstance(other, Soldier):
            soldier_rect = other.get_rect()
            return self._rect.colliderect(soldier_rect)

    def _check_hover(self):
        if self._select:
            self._outline_colour = (255, 0, 0)
        elif self._hover:
            self._outline_colour = (255, 255, 255)
        else:
            self._outline_colour = (207, 185, 151)

    def get_waypoint_graph(self):
        return self._waypoint_graph

    def get_country(self):
        return self._country


class FrontLineTrench(Trench, ABC):
    def __init__(self, width, height, total_capacity, coord, country, ground_colour, actors):
        super().__init__(width, height, total_capacity, coord, country, ground_colour, actors)


class SupportTrench(Trench, ABC):
    def __init__(self, width, height, total_capacity, coord, country, ground_colour, actors):
        super().__init__(width, height, total_capacity, coord, country, ground_colour, actors)
