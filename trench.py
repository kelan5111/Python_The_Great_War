import random
from abc import ABC, abstractmethod
import pygame

from coordinate import Coordinate
from game_mechanics import Actor
from npc import Soldier, FightingDirection
from waypoint import Graph


class Trench(Actor, ABC):
    def __init__(self, coord, width, height, total_capacity, country, ground_colour, npc_list, group):
        super().__init__(coord, width, height, group)
        self._coord = coord
        self._width = width
        self._height = height

        self._outline_colour = (207, 185, 151)
        self._ground_colour = ground_colour

        self._boarder_rect = pygame.Rect(coord.get_coord(), (self._width, height))

        self._line_x = self._rect.topleft[0] - 10, self._rect.topright[0]
        self._line_y = self._rect.topleft[1], self._rect.bottomleft[1]

        self._start_line_one = self._rect.topleft
        self._end_line_one = self._rect.bottomleft
        self._start_line_two = self._rect.topright
        self._end_line_two = self._rect.bottomright

        self._line_start_two = self._rect
        self._line_end_two = None

        self._line_list = []

        self._waypoint_graph = Graph(self._width, height, 20)
        self._build_waypoints()

        self._total_capacity = total_capacity
        self._country = country
        self._curr_soldiers = []

        self._npc_list = npc_list

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

    def _build_waypoints(self):
        self._waypoint_graph.build(self._line_x, self._line_y)

    def _update_curr_soldiers(self):
        for actor in self._npc_list:
            if self.has_collided(actor) and self.has_selected():
                if actor not in self._curr_soldiers:
                    self._curr_soldiers.append(actor)

    def _check_hover(self):
        if self._select:
            self._outline_colour = (255, 0, 0)
        elif self._hover:
            self._outline_colour = (255, 255, 255)
        else:
            self._outline_colour = (207, 185, 151)

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
    def __init__(self, from_trench, to_trench, total_capacity, country, ground_colour, npc_list, group, coord=Coordinate(0, 0), width=0, height=0):
        super().__init__(coord, width, height, total_capacity, country, ground_colour, npc_list, group)

        self._from_trench = from_trench
        self._to_trench = to_trench
        self._fighting_direction = country.value[1]

        self._build()

    def draw(self, screen, camera):
        for from_coord, to_coord in self._lines:
            screen_from_coord = camera.translate_coord(from_coord)
            screen_to_coord = camera.translate_coord(to_coord)

            pygame.draw.line(screen, self._outline_colour, screen_from_coord, screen_to_coord, 2)

    def _build(self):
        line_start = None
        line_end = None

        if self._fighting_direction == FightingDirection.WEST:
            line_start = self._from_trench.get_line_two_coord()[1]
            line_end = self._to_trench.get_line_one_coord()[0]

        elif self._fighting_direction == FightingDirection.EAST:
            line_start = self._from_trench.get_line_one_coord()[1]
            line_end = self._to_trench.get_line_two_coord()[0]

        line_one_start = line_start[0], line_start[1] // 2
        line_one_end = line_end[0], line_start[1] // 2

        line_two_start = line_one_start[0], line_one_start[1] - 20
        line_two_end = line_one_end[0], line_one_end[1] - 20

        self._lines = [[line_one_start, line_one_end], [line_two_start, line_two_end]]

        self._calc_diameter()

        '''while current_coord[0] < end_coord[0]:
            distance = random.randint(0, 10)
            next_x = current_coord[0] + distance
            next_y = current_coord[1] + distance

            self._lines.append((next_x, next_y))'''

    def _calc_diameter(self):
        fl_trench_prox_end = self._from_trench.get_proximity()[0]
        sl_trench_prox_start = self._to_trench.get_proximity()[0]

        fl_trench_prox_end_coord = Coordinate(fl_trench_prox_end[0], fl_trench_prox_end[1])

        self._width = fl_trench_prox_end_coord.calculate_distance(sl_trench_prox_start)
        self._height = self._to_trench.get_height() // 2

    def _calc_line_one(self):
        line_one = self._from_trench.get_line_one_coord()
        line_two = self._to_trench.get_line_one_coord()

        if self._fighting_direction.value == 0:
            pass
        elif self._fighting_direction.value == 1:
            pass

        self._width = None


    def _calc_line_two(self):
        pass
