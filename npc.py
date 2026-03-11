import pygame
from enum import Enum
from coordinate import Coordinate, Direction
from abc import ABC, abstractmethod
from game_mechanics import Actor, Timer
import random


class NPC(Actor):
    ID = 0
    SPEED = 0.5
    SIZE = 20

    def __init__(self, coord, width, height, waypoint_graph, country, group):
        super().__init__(coord, width, height, group)
        self._width = NPC.SIZE
        self._height = NPC.SIZE
        self._country = country
        self._colour = country.value[0]
        self._border_colour = (0, 0, 0)
        self._regiment_colour = (0, 0, 0)
        self._rect = pygame.Rect(self._world_coord.get_coord(), (self._width, self._height))
        self._ID = NPC.ID + 1

        self._speed = NPC.SPEED
        self._actors = group.get_actors()

        self._engaged = False
        self._moving = False
        self._idle = True

        self._path = []
        self._curr_waypoint_graph = waypoint_graph
        self._next_waypoint_graph = None
        self._target_waypoint = None

        if coord is not None:
            self._curr_waypoint = self._curr_waypoint_graph.find_nearest_waypoint(coord.get_coord())
            self._world_coord = self._curr_waypoint.get_coord()

    def draw(self, screen, camera):
        screen_rect = camera.translate_rect(self._rect)
        border_thickness = 2

        if self._select:
            self._border_colour = (255, 255, 255)
        else:
            self._border_colour = self._regiment_colour

        pygame.draw.rect(screen, self._colour, screen_rect)
        pygame.draw.rect(screen, self._border_colour, screen_rect, border_thickness)

    def act(self, mouse_pos):
        self._execute_idle_movement()
        self._execute_player_movement()

    def _execute_idle_movement(self):
        if self._idle and not self._moving:
            neighbours = self._curr_waypoint.get_neighbours()
            next_coord = random.choice(neighbours).get_coord()
            self.set_path(next_coord)

    def _execute_player_movement(self):
        if not self._engaged:
            if self._target_waypoint is None:
                if self._path:
                    self._target_waypoint = self._path.pop()
                else:
                    if self._next_waypoint_graph is not None:
                        self._switch_waypoint_graph()

                    self._moving = False
                    return

            target_coord = self._target_waypoint.get_coord()

            if self._world_coord.get_coord() == target_coord.get_coord():
                self._curr_waypoint = self._target_waypoint
                self._target_waypoint = None
                return

            next_coord = self._calc_next_move(target_coord)
            self._update_rect(next_coord)

    def set_path(self, target_coord=None, waypoint_id=None):
        if target_coord is not None:  # If we want to move to a certain coord (find the closest waypoint)
            self._target_waypoint = self._curr_waypoint_graph.find_nearest_waypoint(target_coord)
            path = self._curr_waypoint_graph.build_path([self._target_waypoint], waypoint_id, self._curr_waypoint,
                                                        self._target_waypoint)
        else:
            path = self._curr_waypoint_graph.build_path([], waypoint_id, self._curr_waypoint, None)

        if path is not None:
            self._moving = True
            self._path = path
            self._target_waypoint = None
        else:
            self._moving = False

    def _calc_next_move(self, target_coord):
        step = 1
        new_x = self._world_coord.get_x()
        new_y = self._world_coord.get_y()
        target_x = target_coord.get_x()
        target_y = target_coord.get_y()

        if new_x < target_x:
            new_x += (step * NPC.SPEED)
        elif new_x > target_x:
            new_x -= (step * NPC.SPEED)

        if new_y < target_y:
            new_y += (step * NPC.SPEED)
        elif new_y > target_y:
            new_y -= (step * NPC.SPEED)

        return Coordinate(new_x, new_y)

    def _is_enemy_near(self, enemy):
        if enemy.get_country() != self._country:
            enemy_coord = enemy.get_coord()
            danger = self._world_coord.execute_radius_check(enemy_coord)
            if danger:
                return enemy

        return None

    def _switch_waypoint_graph(self):
        print(True)
        # Swap the current with the new graph after current path is finished
        self._curr_waypoint_graph = self._next_waypoint_graph
        self._next_waypoint_graph = None

        self.set_path(self._world_coord)

    @abstractmethod
    def _attack(self):
        pass

    def _update_rect(self, coord):
        self._world_coord = coord
        self._rect = pygame.Rect(self._world_coord.get_coord(), (self._width, self._height))

    def set_idle(self, idle):
        self._idle = idle

    def set_next_waypoint_graph(self, waypoint_graph):
        self._next_waypoint_graph = waypoint_graph

    def get_curr_waypoint_graph(self):
        return self._curr_waypoint_graph

    def get_country(self):
        return self._country

    def is_idle(self):
        return self._idle


class Soldier(NPC):
    def __init__(self, coord, width, height, curr_waypoint_graph, country, group, weapon=None):
        super().__init__(coord, width, height, curr_waypoint_graph, country, group)

        self._country = country
        self._regiment_colour = self._colour
        self._weapon = weapon
        self._enemy_lock = None
        self._shot_chance = 100

    def __str__(self):
        return f"Soldier: {self._ID}, Country: {self._country}, Waypoint: {self._curr_waypoint}"

    def act(self, mouse_pos):
        super().act(mouse_pos)

        if not self._idle:
            self._detect_enemies()

    def kill(self):
        self._alive = False
        self._remove_weapon()

    def _detect_enemies(self):
        for actor in self._actors:
            if isinstance(actor, Soldier):
                if actor.get_country() != self._country:
                    enemy = self._is_enemy_near(actor)

                    if enemy is not None:  # Enemy is near, stop moving and engage
                        self._engaged = True
                        self._enemy_lock = enemy
                        self._attack()
                    else:  # No enemy is in sight act normal
                        self._engaged = False
                        self._enemy_lock = None

    def _attack(self):
        if self.has_weapon():
            shot_success = self._calc_shot_chance()
            if shot_success:
                self._weapon.shoot(self._enemy_lock)

    def _calc_shot_chance(self):
        if self.has_weapon():
            random_chance = random.randint(0, 100)
            moving = 30

            # Negative factors contributing to the shot chance
            if self._moving:
                self._shot_chance -= moving

            # Measuring the chances against random num
            if random_chance <= self._shot_chance:
                return True

        return False

    def set_weapon(self, weapon):
        weapon.set_owner(self)
        self._weapon = weapon

    def _remove_weapon(self):
        self._weapon.remove_owner()

    def has_weapon(self):
        return self._weapon is not None

    def get_weapon(self):
        return self._weapon

    def get_shot_chance(self):
        return self._shot_chance


class SpecialForces(Soldier):
    def __init__(self, coord, width, height, curr_waypoint_graph, country, group):
        super().__init__(coord, width, height, curr_waypoint_graph, country, group)

        self._skill_lvl = 0

    def get_skill_lvl(self):
        return self._skill_lvl


class Gunners(SpecialForces):
    def __init__(self, coord, width, height, curr_waypoint_graph, country, group):
        super().__init__(coord, width, height, curr_waypoint_graph, country, group)

        self._regiment_colour = (0, 0, 153)


class FightingDirection(Enum):
    WEST = 0
    EAST = 1


class Country(Enum):
    BRITAIN = (pygame.color.Color(107, 94, 65), FightingDirection.WEST)
    GERMANY = (pygame.color.Color(75, 83, 72), FightingDirection.EAST)


class WeaponType(Enum):
    pass
