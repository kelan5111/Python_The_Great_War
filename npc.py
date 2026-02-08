import pygame
from enum import Enum
from coordinate import Coordinate
from abc import ABC, abstractmethod


class NPC:
    ID = 0
    WIDTH = 50
    HEIGHT = 50

    def __init__(self, waypoint, country):
        self._curr_waypoint = waypoint
        self._coord = waypoint.get_coord()
        self._country = country
        self._colour = country.value
        self._shape = pygame.Rect(self._coord.get_coord(), (NPC.WIDTH, NPC.HEIGHT))
        self._ID = NPC.ID + 1

        self._path = []
        self._target_waypoint = None

    def draw(self, screen):
        pygame.draw.rect(screen, self._colour, self._shape)
        self.update()

    def set_path(self, waypoint_graph, target_coord=None, waypoint_id=None):
        if target_coord is not None:   # If we want to move to a certain coord (find the closest waypoint)
            self._target_waypoint = waypoint_graph.find_nearest_waypoint(target_coord)
            path = waypoint_graph.build_path([], waypoint_id, self._curr_waypoint, self._target_waypoint)
        else:
            path = waypoint_graph.build_path([], waypoint_id, self._curr_waypoint, None)

        if path is not None:
            self._path = path
            self._target_waypoint = None

    def update(self):
        if self._target_waypoint is None:
            if self._path:
                self._target_waypoint = self._path.pop()
            else:
                return

        target_coord = self._target_waypoint.get_coord()

        if self._coord.get_coord() == target_coord.get_coord():
            self._curr_waypoint = self._target_waypoint
            self._target_waypoint = None
            return

        next_coord = self._calc_next_coord(target_coord)
        self._update(next_coord)

    def _calc_next_coord(self, target_coord):
        step = 1
        new_x = self._coord.get_x()
        new_y = self._coord.get_y()
        target_x = target_coord.get_x()
        target_y = target_coord.get_y()

        if new_x < target_x:
            new_x += step
        elif new_x > target_x:
            new_x -= step

        if new_y < target_y:
            new_y += step
        elif new_y > target_y:
            new_y -= step

        return Coordinate(new_x, new_y)

    def _is_enemy_near(self, enemy):
        for e in enemy:
            danger = self._coord.perform_radius_check(e.get_coord())
            if danger:
                return e

        return None

    @abstractmethod
    def _attack(self):
        pass

    def _update(self, coord):
        self._coord = coord
        self._shape.x = self._coord.get_x()
        self._shape.y = self._coord.get_y()

    # Setters and getters


class Soldier(NPC, ABC):
    def __init__(self, waypoint, country):
        super().__init__(waypoint, country)

        self._curr_waypoint = waypoint
        self._country = country

        self._selected = False

    def __str__(self):
        return f"Soldier: {self._ID}, Country: {self._country}, Waypoint: {self._curr_waypoint}, target: {self._path}"

    def detect_enemy(self, soldier_list):
        enemy = self._is_enemy_near(soldier_list)

        if enemy is not None:
            self.__execute_attack(enemy)

    def draw(self, screen):
        pygame.draw.rect(screen, self._colour, self._shape)
        self.update()

        if self._selected:
            border_thickness = 5
            border_color = (255, 255, 255)
            pygame.draw.rect(screen, border_color, self._shape, border_thickness)

    def __execute_attack(self, target):
        pass

    def has_selected(self):
        return self._selected

    def select(self, mouse_pos):
        if self._shape.collidepoint(mouse_pos):
            self._selected = True

    def unselect(self):
        self._selected = False


class Country(Enum):
    BRITAIN = pygame.color.Color(255, 0, 0)
    GERMANY = pygame.color.Color(127, 127, 127)
