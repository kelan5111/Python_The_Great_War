import pygame
from enum import Enum
from coordinate import Coordinate
from abc import ABC, abstractmethod
from game_mechanics import Actor
import random


class NPC(Actor):
    ID = 0
    SPEED = 0.5

    def __init__(self, coord, width, height, waypoint_graph, country, actors):
        super().__init__(coord, width, height)
        self._width = width
        self._height = height
        self._country = country
        self._colour = country.value
        self._rect = pygame.Rect(self._coord.get_coord(), (self._width, self._height))
        self._ID = NPC.ID + 1

        self._speed = NPC.SPEED
        self._actors = actors

        self._engaged = False
        self._moving = False
        self._idle = True

        self._path = []
        self._curr_waypoint_graph = waypoint_graph
        self._next_waypoint_graph = None
        self._target_waypoint = None

        self._curr_waypoint = self._curr_waypoint_graph.find_nearest_waypoint(coord.get_coord())
        self._coord = self._curr_waypoint.get_coord()

    def draw(self, screen):
        pygame.draw.rect(screen, self._colour, self._rect)

        if self._select:
            border_thickness = 2
            border_color = (255, 255, 255)
            pygame.draw.rect(screen, border_color, self._rect, border_thickness)

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

            if self._coord.get_coord() == target_coord.get_coord():
                self._curr_waypoint = self._target_waypoint
                self._target_waypoint = None
                return

            next_coord = self._calc_next_move(target_coord)
            self._update(next_coord)

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
        new_x = self._coord.get_x()
        new_y = self._coord.get_y()
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
            danger = self._coord.execute_radius_check(enemy_coord)
            if danger:
                return enemy

        return None

    def _switch_waypoint_graph(self):
        print(True)
        # Swap the current with the new graph after current path is finished
        self._curr_waypoint_graph = self._next_waypoint_graph
        self._next_waypoint_graph = None

        self.set_path(self._coord)

    @abstractmethod
    def _attack(self):
        pass

    def _update(self, coord):
        self._coord = coord
        self._rect = pygame.Rect(self._coord.get_coord(), (self._width, self._height))

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
    def __init__(self, coord, width, height, curr_waypoint_graph, country, actors, weapon):
        super().__init__(coord, width, height, curr_waypoint_graph, country, actors)

        self._country = country
        self._weapon = weapon
        self._enemy_lock = None
        self._shot_chance = 100

    def __str__(self):
        return f"Soldier: {self._ID}, Country: {self._country}, Waypoint: {self._curr_waypoint}"

    def act(self, mouse_pos):
        super().act(mouse_pos)

        self._detect_enemies()
        self._weapon.lock_to_owner(self._coord)

    def _detect_enemies(self):
        for actor in self._actors:
            if isinstance(actor, Soldier):
                enemy = self._is_enemy_near(actor)

                if enemy is not None:  # Enemy is near, stop moving and engage
                    self._engaged = True
                    self._enemy_lock = enemy
                    self._attack()
                else:  # No enemy is in sight act normal
                    self._engaged = False
                    self._enemy_lock = None

    def _draw_weapon(self):
        if self.has_weapon():
            self._weapon.show()

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
        self._weapon = weapon

    def remove_weapon(self):
        self._weapon.kill()

    def has_weapon(self):
        return self._weapon is not None

    def get_weapon(self):
        return self._weapon

    def get_rect(self):
        return self._rect

    def get_shot_chance(self):
        return self._shot_chance


class Weapon(Actor):
    AMMO_CAPACITY = 20
    WIDTH = 10
    HEIGHT = 20

    def __init__(self, gun_type, coord=Coordinate(-100, -100)):
        super().__init__(coord, width=0, height=0)
        self._colour = pygame.Color(0, 0, 0)

        self._gun_type = gun_type
        self._ammo = Weapon.AMMO_CAPACITY
        self._coord = coord

    def __str__(self):
        return f"Gun{self._gun_type}: capacity: {self._ammo}"

    def draw(self, screen):
        pygame.draw.rect(screen, self._colour, self._rect)

    def act(self, mouse_pos):
        self._rect = pygame.Rect(self._coord.get_coord(), (Weapon.WIDTH, Weapon.HEIGHT))

    def lock_to_owner(self, coord):
        self._coord = coord

    def shoot(self, target):
        target.remove_weapon()
        target.kill()
        # need a weapon chance of killing


class Country(Enum):
    BRITAIN = pygame.color.Color(255, 0, 0)
    GERMANY = pygame.color.Color(127, 127, 127)


class WeaponType(Enum):
    pass
