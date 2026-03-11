import pygame
import random
from abc import ABC, abstractmethod

from game_mechanics import Actor, Timer
from npc import Coordinate, Gunners, FightingDirection


class Weapon(Actor):
    def __init__(self, coord, width, height, shot_range, shot_speed, ammo_capacity, group):
        super().__init__(coord, width, height, group)
        self._colour = pygame.Color(0, 0, 0)
        self._world_coord = coord

        self._shot_range = shot_range
        self._shot_speed = shot_speed
        self._shot_chance = 0
        self._ammo_capacity = ammo_capacity

        self._active_projectile = []
        self._owner = None
        self._country = None

    def __str__(self):
        pass

    def draw(self, screen, camera):
        screen_rect = camera.translate_rect(self._rect)
        pygame.draw.rect(screen, self._colour, screen_rect)
        # Draw bullets
        if len(self._active_projectile) > 0:
            for projectile in self._active_projectile:
                projectile.draw(screen, camera)

    def act(self, *args):
        self._update_rect()
        self._lock_to_owner()
        self._update_projectile()

    @abstractmethod
    def shoot(self, *args):
        pass

    @abstractmethod
    def reload(self, *args):
        pass

    def _update_rect(self):
        self._rect = pygame.Rect(self._world_coord.get_coord(), (self._width, self._height))

    def _lock_to_owner(self):
        if self._owner is not None:
            new_x = self._owner.get_x()
            new_y = self._owner.get_y()

            self._world_coord = Coordinate(new_x, new_y)

    def _update_projectile(self):
        for p in self._active_projectile:
            p.update()

            if p.is_finished():
                self._active_projectile.remove(p)

    def set_owner(self, owner):
        self._owner = owner
        self._country = owner.get_country()

    def remove_owner(self):
        self._owner = None

    def get_owner(self):
        return self._owner


class Artillery(Weapon):
    def __init__(self, coord, width, height, shot_range, shot_speed, ammo_capacity, friendly_st, enemy_st,
                 group, field_waypoint_graph, country):
        super().__init__(coord, width, height, shot_range, shot_speed, ammo_capacity, group)

        self._shot_speed = 0
        self._shot_x = 0
        self._shot_y = 0

        self._shell_supply = ammo_capacity
        self._field_waypoint_graph = field_waypoint_graph
        self._country = country
        self._fighting_direction = country.value[1]

        self._friendly_st_coord = friendly_st
        self._enemy_st_coord = enemy_st

        self._max_gunner = 6
        self._timer = Timer()
        self._gunners = []
        self._barrage_coord = None

        self.fill_gunners(group)  # spawn gunners at start

    def draw(self, screen, camera):
        super().draw(screen, camera)

    def act(self, mouse_pos):
        super().act()

        self._fire_random_projectile()

    def shoot(self, target_coord):
        start_x = self._world_coord.get_x()
        start_y = self._world_coord.get_y()

        shell = Projectile(Coordinate(start_x, start_y), target_coord, 5)
        self._active_projectile.append(shell)

    def _fire_random_projectile(self):
        if len(self._gunners) > 0:
            if self._timer.is_finished(10):
                self._barrage_coord = self._calc_projectile_shot()

                self.shoot(self._barrage_coord)

                self._timer.reset()

    def reload(self):
        pass

    def _calc_projectile_shot(self):
        positive_reward = 20
        negative_reward = -20
        balance_reward = 0

        if self._fighting_direction == FightingDirection.EAST.value:
            projectile_start_x = self._enemy_st_coord[0]
            projectile_end_x = self._friendly_st_coord[0]
            projectile_start_y = self._enemy_st_coord[1]
            projectile_end_y = self._friendly_st_coord[1]
        else:
            projectile_start_x = self._friendly_st_coord[0]
            projectile_end_x = self._enemy_st_coord[0]
            projectile_start_y = self._friendly_st_coord[1]
            projectile_end_y = self._enemy_st_coord[1]

        min_x = min(projectile_start_x, projectile_end_x)
        max_x = max(projectile_start_x, projectile_end_x)
        min_y = min(projectile_start_y, projectile_end_y)
        max_y = max(projectile_start_y, projectile_end_y)

        self._shot_x = random.randint(min_x, max_x)
        self._shot_y = random.randint(min_y, max_y)

        return Coordinate(self._shot_x, self._shot_y)

    def add_soldier(self, soldier):
        if isinstance(soldier, Gunners):  # soldiers must be Gunners (special force)
            self._gunners.append(soldier)

    def fill_gunners(self, group):
        for gunner in range(self._max_gunner):
            starting_pos = self._world_coord
            gunner = Gunners(starting_pos, 0, 0, self._field_waypoint_graph, self._country, group)
            gunner.set_idle(False)

            self.add_soldier(gunner)

    def remove_soldier(self, soldier):
        self._gunners.remove(soldier)

    def get_soldiers(self):
        return self._max_gunner


class Gun(Weapon):
    def __init__(self, coord, width, height, gun_type, shot_range, shot_speed, ammo_capacity, group):
        super().__init__(coord, width, height, shot_range, shot_speed, ammo_capacity, group)

        self._gun_type = gun_type
        self._magazine_capacity = 10

    def shoot(self, target):
        if self._magazine_capacity != 0 or self._ammo_capacity != 0:
            self._magazine_capacity -= 1
            target.kill()

    def reload(self):
        pass


class Projectile:
    def __init__(self, start_coord, target_coord, speed):
        self._radius = 10
        self._colour = (0, 0, 0)
        self._speed = speed

        self._world_coord = start_coord
        self._target_coord = target_coord

        self._finished = False

    def draw(self, screen, camera):
        screen_coord = camera.translate_coord(self._world_coord.get_coord())

        if not self._finished:
            pygame.draw.circle(screen, self._colour, screen_coord, self._radius)

    def update(self):
        self._move()

    def _move(self):
        if self._target_coord is not None:

            next_coord = self._calc_next_move(self._target_coord)

            self._world_coord = next_coord

            if self._world_coord.calculate_distance(self._target_coord) < 10:
                self._finished = True

    def _calc_next_move(self, target_coord):
        step = 1
        new_x = self._world_coord.get_x()
        new_y = self._world_coord.get_y()
        target_x = target_coord.get_x()
        target_y = target_coord.get_y()

        if new_x < target_x:
            new_x += (step * self._speed)
        elif new_x > target_x:
            new_x -= (step * self._speed)

        if new_y < target_y:
            new_y += (step * self._speed)
        elif new_y > target_y:
            new_y -= (step * self._speed)

        return Coordinate(new_x, new_y)

    def is_finished(self):
        return self._finished
