import random
from abc import ABC, abstractmethod
import pygame

from coordinate import Coordinate
from game_mechanics import Actor
from npc import Soldier, FightingDirection
from waypoint import Graph


class Trench(Actor):
    def __init__(self, coord, width, height, total_capacity, country, ground_colour, npc_list, group):
        super().__init__(coord, width, height, group)
        self._coord = coord
        self._width = width
        self._height = height

        self._outline_colour = (207, 185, 151)
        self._ground_colour = ground_colour
        self._total_capacity = total_capacity
        self._country = country
        self._fighting_direction = country.value["fighting_direction"]

        self._boarder_rect = pygame.Rect(coord.get_coord(), (self._width, height))

        self._line_x = self._rect.topleft[0] - 10, self._rect.topright[0]
        self._line_y = self._rect.topleft[1], self._rect.bottomleft[1]

        self._start_line_one = self._rect.topleft
        self._end_line_one = self._rect.bottomleft
        self._start_line_two = self._rect.topright
        self._end_line_two = self._rect.bottomright

        self._line_list = []
        self._comm_trenches = []

        self._waypoint_graph = Graph(self._width, height, 20)
        self._waypoint_graph.build(self._line_x, self._line_y)

        self._curr_soldiers = []
        self._npc_list = npc_list

        self._waypoint_graph.set_debug(True)

    def draw(self, screen, camera):
        screen_rect = camera.translate_rect(self._rect)

        screen_start_line_one = camera.translate_coord(self._start_line_one)
        screen_end_line_one = camera.translate_coord(self._end_line_one)

        screen_start_line_two = camera.translate_coord(self._start_line_two)
        screen_end_line_two = camera.translate_coord(self._end_line_two)

        # Draw the outline of the trench
        pygame.draw.line(screen, self._outline_colour, screen_start_line_one, screen_end_line_one, 5)
        pygame.draw.line(screen, self._outline_colour, screen_start_line_two, screen_end_line_two, 5)
        # Drawing the trench's ground
        pygame.draw.rect(screen, self._ground_colour, screen_rect)

        self._waypoint_graph.draw(screen, camera)

    def act(self, mouse_pos):
        self._update_curr_soldiers()
        self._update_rect()

        self._hover = self._rect.collidepoint(mouse_pos)

        self._check_hover()

    def _update_rect(self):
        self._rect = pygame.Rect(self._coord.get_coord(), (self._width, self._height))
        self._boarder_rect = pygame.Rect(self._coord.get_coord(), (self._width, self._height))

    def _update_curr_soldiers(self):
        for npc in self._npc_list:
            if self.has_collided(npc):
                self._curr_soldiers.append(npc)

            if npc in self._curr_soldiers and not self.has_collided(npc):
                self._curr_soldiers.remove(npc)

    def _check_hover(self):
        if self._select:
            self._outline_colour = (255, 0, 0)
        elif self._hover:
            self._outline_colour = (255, 255, 255)
        else:
            self._outline_colour = (207, 185, 151)

    def calc_entrance_points(self):
        pass

    def add_comm_trenches(self, comm_trench):
        self._comm_trenches.append(comm_trench)

    def get_comm_trenches(self):
        return self._comm_trenches

    @abstractmethod
    def _build(self):
        pass

    def set_debug(self, debug):
        self._waypoint_graph.set_debug(debug)

    def get_proximity(self):
        return [self._line_x, self._line_y]

    def get_line_one_coord(self):
        return self._start_line_one, self._end_line_one

    def get_line_two_coord(self):
        return self._start_line_two, self._end_line_two

    def get_waypoint_graph(self):
        return self._waypoint_graph

    def get_country(self):
        return self._country

    def get_fighting_direction(self):
        return self._fighting_direction


class FrontLineTrench(Trench, ABC):
    def __init__(self, coord, width, height, total_capacity, country, ground_colour, npc_actors, group):
        super().__init__(coord, width, height, total_capacity, country, ground_colour, npc_actors, group)

    def _build(self):
        pass


class SupportTrench(Trench, ABC):
    def __init__(self, coord, width, height, total_capacity, country, ground_colour, npc_actors, group):
        super().__init__(coord, width, height, total_capacity, country, ground_colour, npc_actors, group)

    def _build(self):
        pass

    def recruit(self):
        pass


class CommunicationTrench(Trench):
    def __init__(self, from_trench, to_trench, total_capacity, country, ground_colour, npc_list, group,
                 coord=Coordinate(0, 0), width=0, height=0):
        super().__init__(coord, width, height, total_capacity, country, ground_colour, npc_list, group)

        self._from_trench = from_trench
        self._to_trench = to_trench

        self._entrance_points = {}

        self._build()
        self._waypoint_graph = Graph(self._width, self._height, 20)
        self._waypoint_graph.build(self._line_x, self._line_y)

        self._waypoint_graph.set_debug(True)

    def draw(self, screen, camera):
        for from_coord, to_coord in self._lines:
            screen_from_coord = camera.translate_coord(from_coord)
            screen_to_coord = camera.translate_coord(to_coord)

            pygame.draw.line(screen, self._outline_colour, screen_from_coord, screen_to_coord, 2)

        self._waypoint_graph.draw(screen, camera)

    def _build(self):
        line_start = None
        line_start_bottom = None
        line_end = None

        # 1. Get the Top and Bottom coords to find the true middle
        if self._fighting_direction == FightingDirection.WEST:
            line_start = self._from_trench.get_line_two_coord()[0]  # Top Right
            line_start_bottom = self._from_trench.get_line_two_coord()[1]   # Bottom Right
            line_end = self._to_trench.get_line_one_coord()[0]  # Top Left

        elif self._fighting_direction == FightingDirection.EAST:
            line_start = self._from_trench.get_line_one_coord()[0]  # Top Left
            line_start_bottom = self._from_trench.get_line_one_coord()[1]   # Bottom Left
            line_end = self._to_trench.get_line_two_coord()[0]  # Top Right

        mid_y = (line_start[1] + line_start_bottom[1]) // 2

        line_one_start = line_start[0], mid_y
        line_one_end = line_end[0], mid_y

        line_two_start = line_one_start[0], line_one_start[1] - 20
        line_two_end = line_one_end[0], line_one_end[1] - 20

        self._lines = [[line_one_start, line_one_end], [line_two_start, line_two_end]]

        self._calc_diameter()

        entrance_one = self._rect.topleft
        entrance_two = self._rect.topright

        self._entrance_points["left_entrance"] = entrance_one
        self._entrance_points["right_entrance"] = entrance_two

    def _calc_diameter(self):
        line_one_start, line_one_end = self._lines[0]
        line_two_start, line_two_end = self._lines[1]

        left_x = min(line_one_start[0], line_one_end[0])
        top_y = min(line_one_start[1], line_two_start[1])

        self._width = abs(line_one_start[0] - line_one_end[0])
        self._height = 20

        self._rect = pygame.Rect(left_x, top_y, self._width, self._height)

        self._line_x = (self._rect.left, self._rect.right)
        self._line_y = (self._rect.top, self._rect.bottom)

    def get_entrance_points(self):
        return self._entrance_points

    def get_from_trench(self):
        return self._from_trench

    def to_trench(self):
        return self._to_trench