import pygame
from enum import Enum
from coordinate import Coordinate, Direction
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
        self._rect = pygame.Rect(self._world_coord.get_coord(), (self._width, self._height))
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
        self._world_coord = self._curr_waypoint.get_coord()

    def draw(self, screen, camera):
        screen_rect = camera.translate_rect(self._rect)

        pygame.draw.rect(screen, self._colour, screen_rect)

        if self._select:
            border_thickness = 2
            border_color = (255, 255, 255)
            pygame.draw.rect(screen, border_color, screen_rect, border_thickness)

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
        self._weapon.lock_to_owner(self._world_coord)

    def kill(self):
        self._alive = False
        self._remove_weapon()

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

    def _remove_weapon(self):
        self._weapon.kill()

    def has_weapon(self):
        return self._weapon is not None

    def get_weapon(self):
        return self._weapon

    def get_shot_chance(self):
        return self._shot_chance


class Weapon(Actor):
    def __init__(self, coord, width, height, shot_range, shot_speed, ammo_capacity):
        super().__init__(coord, width, height)
        self._colour = pygame.Color(0, 0, 0)
        self._world_coord = coord

        self._shot_range = shot_range
        self._shot_speed = shot_speed
        self._shot_chance = 0
        self._ammo_capacity = ammo_capacity

    def __str__(self):
        pass

    def draw(self, screen, camera):
        if self._alive:
            screen_rect = camera.translate_rect(self._rect)
            pygame.draw.rect(screen, self._colour, screen_rect)

    def act(self, mouse_pos):
        self._update_rect()

    @abstractmethod
    def _shoot(self, target):
        pass

    @abstractmethod
    def _reload(self):
        pass

    def _update_rect(self):
        self._rect = pygame.Rect(self._world_coord.get_coord(), (self._width, self._height))

    def lock_to_owner(self, owner_coord):
        new_x = owner_coord.get_x()
        new_y = owner_coord.get_y()

        self._world_coord = Coordinate(new_x, new_y)
        # need a weapon chance of killing


class Artillery(Weapon):
    def __init__(self, coord, width, height, shot_range, shot_speed, ammo_capacity):
        super().__init__(coord, width, height, shot_range, shot_speed, ammo_capacity)

        self._shot_radius = 5  # I need a radius to determine what area gets affected by the impact
        self._shot_speed = 0

    def act(self, mouse_pos):
        self._rect = pygame.Rect(self._world_coord.get_coord(), (self._width, self._height))

    def _shoot(self, target):
        pass

    def _reload(self):
        pass


class Gun(Weapon):
    def __init__(self, coord, width, height, gun_type, shot_range, shot_speed, ammo_capacity):
        super().__init__(coord, width, height, shot_range, shot_speed, ammo_capacity)

        self._gun_type = gun_type
        self._magazine_capacity = 10

    def _shoot(self, target):
        if self._magazine_capacity != 0 or self._ammo_capacity != 0:
            target.kill()

            self._magazine_capacity -= 1

    def _reload(self):
        pass


class Country(Enum):
    BRITAIN = pygame.color.Color(255, 0, 0)
    GERMANY = pygame.color.Color(127, 127, 127)


class WeaponType(Enum):
    pass
