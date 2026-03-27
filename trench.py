import random
from abc import ABC, abstractmethod
import pygame

from coordinate import Coordinate
from game_mechanics import Actor, Timer
from npc import Soldier, FightingDirection
from waypoint import Graph
from fortifications import Sandbag


class Trench(Actor):
    def __init__(self, coord, width, height, total_capacity, country, ground_colour, npc_list, group):
        super().__init__(coord, width, height, group)
        self._coord = coord
        self._width = width
        self._height = height

        self._outline_colour = (207, 185, 151)
        self._ground_colour = ground_colour
        self._max_capacity = total_capacity
        self._sandbag_list = []
        self._country = country
        self._fighting_direction = country.value["fighting_direction"]

        self._boarder_rect = pygame.Rect(coord.get_coord(), (self._width, height))

        self._line_x = self._rect.topleft[0] - 10, self._rect.topright[0]
        self._line_y = self._rect.topleft[1], self._rect.bottomleft[1]

        self._start_line_one = self._rect.topleft
        self._end_line_one = self._rect.bottomleft
        self._start_line_two = self._rect.topright
        self._end_line_two = self._rect.bottomright

        self._line_list = {}
        self._comm_trenches = []

        self._waypoint_graph = Graph(self._width, height, 20)
        self._waypoint_graph.build(self._line_x, self._line_y)

        self._curr_soldiers = []
        self._npc_list = npc_list

        self._debug = False

    def draw(self, screen, camera):
        for key, (start_point, end_point) in self._line_list.items():

            screen_from_coord = camera.translate_coord(start_point)
            screen_to_coord = camera.translate_coord(end_point)

            pygame.draw.line(screen, self._outline_colour, screen_from_coord, screen_to_coord, 4)

        screen_rect = camera.translate_rect(self._rect)
        pygame.draw.rect(screen, self._ground_colour, screen_rect)

        if self._debug:
            self._waypoint_graph.draw(screen, camera)

    def _build_sandbags(self, group):
        for key, (start_point, end_point) in self._line_list.items():

            is_vertical = start_point[0] == end_point[0]
            is_horizontal = start_point[1] == end_point[1]

            if is_vertical:
                start_y = min(start_point[1], end_point[1])
                end_y = max(start_point[1], end_point[1])

                current_y = start_y

                while current_y < end_y:
                    new_sandbag = Sandbag(Sandbag.IMAGE_PATH, 0, Coordinate(start_point[0], current_y), 70, 70, group, 10)

                    self._sandbag_list.append(new_sandbag)
                    current_y += random.randint(18, 20)

            elif is_horizontal:
                start_x = min(start_point[0], end_point[0])
                end_x = max(start_point[0], end_point[0])

                current_x = start_x

                while current_x < end_x:
                    new_sandbag = Sandbag(Sandbag.IMAGE_PATH, 90, Coordinate(current_x, start_point[1]), 70, 70, group, 10)

                    self._sandbag_list.append(new_sandbag)
                    current_x += random.randint(18, 20)

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

                npc.set_curr_trench(self)

            if npc in self._curr_soldiers and not self.has_collided(npc):
                self._curr_soldiers.remove(npc)

    def _check_hover(self):
        if self._select:
            self._ground_colour = (90, 90, 90)
        else:
            self._ground_colour = (48, 35, 9)

    def add_comm_trenches(self, comm_trench):
        self._comm_trenches.append(comm_trench)

    def get_comm_trenches(self):
        return self._comm_trenches

    def _build(self, group):
        self._build_lines()
        self._build_sandbags(group)

    def _build_lines(self):
        start_line_one = self._rect.topleft
        start_line_two = self._rect.topright
        finish_line_one = self._rect.bottomleft
        finish_line_two = self._rect.bottomright

        self._line_list["line_one"] = [start_line_one, finish_line_one]
        self._line_list["line_two"] = [start_line_two, finish_line_two]

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

    def get_curr_soldiers(self):
        return self._curr_soldiers

    def get_country(self):
        return self._country

    def get_fighting_direction(self):
        return self._fighting_direction

    def get_max_capacity(self):
        return self._max_capacity


class FrontLineTrench(Trench, ABC):
    def __init__(self, coord, width, height, total_capacity, country, ground_colour, npc_actors, group):
        super().__init__(coord, width, height, total_capacity, country, ground_colour, npc_actors, group)

        self._build(group)


class SupportTrench(Trench, ABC):
    def __init__(self, coord, width, height, total_capacity, country, ground_colour, npc_actors, group):
        super().__init__(coord, width, height, total_capacity, country, ground_colour, npc_actors, group)

        self._build(group)
        self._reinforcement_timer = Timer()

        self._reinforcement = []

    def act(self, mouse_pos):
        super().act(mouse_pos)

        self._monitor_npc()

    def recruit(self):
        pass

    def _monitor_npc(self):
        self._monitor_reinforcement()

    def _monitor_reinforcement(self):
        comm_trench = self._comm_trenches[0]
        support_line_trench, front_line_trench = comm_trench.get_connected_trenches()

        flt_curr_soldiers = front_line_trench.get_curr_soldiers()

        if (len(flt_curr_soldiers) < front_line_trench.get_max_capacity() and
                len(self._curr_soldiers) > 0):

            rand_soldier = random.choice(self._curr_soldiers)

            if rand_soldier not in self._reinforcement:
                self._reinforcement.append(rand_soldier)

            for soldier in self._reinforcement:
                if self._reinforcement_cooldown(4):
                    if rand_soldier.is_idle():
                        rand_soldier.switch_trenches(front_line_trench)

                        self._curr_soldiers.remove(rand_soldier)
                        self._reinforcement.remove(soldier)

    def _reinforcement_cooldown(self, secs):
        if not self._reinforcement_timer.is_started():
            self._reinforcement_timer.start()

        if self._reinforcement_timer.is_finished(secs):
            self._reinforcement_timer.reset()
            return True

        return False


class CommunicationTrench(Trench):
    def __init__(self, from_trench, to_trench, total_capacity, country, ground_colour, npc_list, group,
                 coord=Coordinate(0, 0), width=0, height=0):
        super().__init__(coord, width, height, total_capacity, country, ground_colour, npc_list, group)

        self._connected_trench_one = from_trench
        self._connected_trench_two = to_trench

        self._width = 20

        self._entrance_points = {}

        self._max_capacity = total_capacity

        self._build(group)
        self._waypoint_graph = Graph(self._width, self._height, 20)
        self._waypoint_graph.build(self._line_x, self._line_y)

    def _build_lines(self):
        line_start = None
        line_start_bottom = None
        line_end = None

        # 1. Get the Top and Bottom coords to find the true middle
        if self._fighting_direction == FightingDirection.WEST:
            line_start = self._connected_trench_one.get_line_two_coord()[0]  # Top Right
            line_start_bottom = self._connected_trench_one.get_line_two_coord()[1]  # Bottom Right
            line_end = self._connected_trench_two.get_line_one_coord()[0]  # Top Left

        elif self._fighting_direction == FightingDirection.EAST:
            line_start = self._connected_trench_one.get_line_one_coord()[0]  # Top Left
            line_start_bottom = self._connected_trench_one.get_line_one_coord()[1]  # Bottom Left
            line_end = self._connected_trench_two.get_line_two_coord()[0]  # Top Right

        mid_y = (line_start[1] + line_start_bottom[1]) // 2

        line_one_start = line_start[0], mid_y
        line_one_end = line_end[0], mid_y

        self._height = 30

        line_two_start = line_one_start[0], line_one_start[1] - self._height
        line_two_end = line_one_end[0], line_one_end[1] - self._height

        self._line_list["line_one"] = [line_one_start, line_one_end]
        self._line_list["line_two"] = [line_two_start, line_two_end]

        temp_lines_list = [[line_one_start, line_one_end], [line_two_start, line_two_end]]

        self._calc_diameter(temp_lines_list)

        entrance_one = self._rect.topleft
        entrance_two = self._rect.topright

        self._entrance_points["left_entrance"] = entrance_one
        self._entrance_points["right_entrance"] = entrance_two

    def _calc_diameter(self, temp_lines_list):
        line_one_start, line_one_end = temp_lines_list[0]
        line_two_start, line_two_end = temp_lines_list[1]

        left_x = min(line_one_start[0], line_one_end[0])
        top_y = min(line_one_start[1], line_two_start[1])

        self._width = abs(line_one_start[0] - line_one_end[0])

        self._rect = pygame.Rect(left_x, top_y, self._width, self._height)

        self._line_x = (self._rect.left, self._rect.right)
        self._line_y = (self._rect.top, self._rect.bottom)

    def _monitor_npc(self):
        pass

    def get_entrance_points(self):
        return self._entrance_points

    def get_connected_trenches(self):
        return self._connected_trench_one, self._connected_trench_two
