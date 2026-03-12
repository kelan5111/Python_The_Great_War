import pygame
import random
from abc import ABC, abstractmethod

from game_mechanics import Actor, Timer
from npc import Coordinate, Gunner, FightingDirection, NPC


class Weapon(Actor):
    def __init__(self, coord, width, height, shot_range, shot_speed, ammo_capacity, group):
        super().__init__(coord, width, height, group)
        self._colour = pygame.Color(0, 0, 0)
        self._world_coord = coord

        self._shot_range = shot_range
        self._shot_speed = shot_speed
        self._shot_chance = 0
        self._ammo_capacity = ammo_capacity

        self._timer = Timer()

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
        self._update_projectile()

    @abstractmethod
    def shoot(self, target_coord, npc_list):
        pass

    @abstractmethod
    def reload(self, *args):
        pass

    def _update_rect(self):
        self._rect = pygame.Rect(self._world_coord.get_coord(), (self._width, self._height))

    @abstractmethod
    def _update_projectile(self):
        for p in self._active_projectile:
            p.update()

    def set_owner(self, owner):
        self._owner = owner
        self._country = owner.get_country()

    def remove_owner(self):
        self._owner = None

    def get_owner(self):
        return self._owner


class Artillery(Weapon):
    def __init__(self, coord, width, height, shot_range, shot_speed, ammo_capacity, friendly_slt_coord, enemy_slt_coord,
                 friendly_flt_coord, enemy_flt_coord, group, field_waypoint_graph, country):
        super().__init__(coord, width, height, shot_range, shot_speed, ammo_capacity, group)

        self._shot_speed = 0
        self._shot_x = 0
        self._shot_y = 0

        self._shell_supply = ammo_capacity
        self._field_waypoint_graph = field_waypoint_graph
        self._country = country
        self._fighting_direction = country.value[1]

        self._friendly_slt_coord = friendly_slt_coord
        self._enemy_slt_coord = enemy_slt_coord
        self._friendly_flt_coord = friendly_flt_coord
        self._enemy_flt_coord = enemy_flt_coord

        self._max_gunner = 6
        self._timer = Timer()
        self._gunners = []
        self._barrage_coord = None

    def draw(self, screen, camera):
        super().draw(screen, camera)

    def act(self, mouse_pos):
        super().act()

    def shoot(self, target_coord, npc_list):
        if len(self._gunners) > 0:
            start_x = self._world_coord.get_x()
            start_y = self._world_coord.get_y()

            shell = Shell(Coordinate(start_x, start_y), target_coord, speed=5, blast_factor=10, npc_list=npc_list)
            self._active_projectile.append(shell)

    def shoot_random_projectile(self, npc_list):
        if len(self._gunners) > 0:
            if self._timer.is_finished(10):
                self._barrage_coord = self._calc_projectile_shot()

                self.shoot(self._barrage_coord, npc_list)

                self._timer.reset()

    def reload(self):
        pass

    def _calc_projectile_shot(self):
        positive_reward = 20
        negative_reward = -20
        balance_reward = 0

        if self._fighting_direction == FightingDirection.EAST.value:
            projectile_start_x = self._enemy_slt_coord[0]
            projectile_end_x = self._friendly_flt_coord[0]
            projectile_start_y = self._enemy_slt_coord[1]
            projectile_end_y = self._friendly_flt_coord[1]
        else:
            projectile_start_x = self._friendly_flt_coord[0]
            projectile_end_x = self._enemy_slt_coord[0]
            projectile_start_y = self._friendly_flt_coord[1]
            projectile_end_y = self._enemy_slt_coord[1]

        min_x = min(projectile_start_x, projectile_end_x)
        max_x = max(projectile_start_x, projectile_end_x)
        min_y = min(projectile_start_y, projectile_end_y)
        max_y = max(projectile_start_y, projectile_end_y)

        self._shot_x = random.randint(min_x, max_x)
        self._shot_y = random.randint(min_y, max_y)

        return Coordinate(self._shot_x, self._shot_y)

    def _update_projectile(self):
        super()._update_projectile()

        for shell in self._active_projectile:
            if shell.has_exploded():
                self._active_projectile.remove(shell)

    def add_soldier(self, soldier):
        self._gunners.append(soldier)

    def remove_soldier(self, soldier):
        self._gunners.remove(soldier)

    def get_soldiers(self):
        return self._max_gunner


class Gun(Weapon):
    def __init__(self, coord, width, height, gun_type, shot_range, shot_speed, ammo_capacity, group):
        super().__init__(coord, width, height, shot_range, shot_speed, ammo_capacity, group)

        self._gun_type = gun_type
        self._magazine_capacity = 10

    def act(self, mouse_pos):
        super().act(mouse_pos)

        self._lock_to_owner()

    def shoot(self, target, npc_list):
        if self._magazine_capacity != 0 or self._ammo_capacity != 0:
            start_coord = self._world_coord
            bullet = Projectile(start_coord, target.get_coord(), speed=5, npc_list=npc_list)

            self._active_projectile.append(bullet)
            self._magazine_capacity -= 1

    def _update_projectile(self):
        hits = [projectile for projectile in self._active_projectile
                if projectile.has_hit()]

        if len(hits) > 2:
            [hit.set_mute_sounds(True) for hit in hits]

            self._active_projectile.clear()

    def reload(self):
        pass

    def _lock_to_owner(self):
        if self._owner is not None:
            new_x = self._owner.get_x()
            new_y = self._owner.get_y()

            self._world_coord = Coordinate(new_x, new_y)


class Projectile:
    def __init__(self, start_coord, target_coord, speed, npc_list):
        self._radius = 10
        self._colour = (0, 0, 0)
        self._speed = speed
        self._npc_list = npc_list

        self._world_coord = start_coord
        self._target_coord = target_coord

        self._mute_sounds = False
        self._hit = False
        self._targets_hit = []

    def draw(self, screen, camera):
        screen_coord = camera.translate_coord(self._world_coord.get_coord())

        if not self._hit:
            pygame.draw.circle(screen, self._colour, screen_coord, self._radius)

    def update(self):
        self._move()
        self._check_targets_hit()

    def _move(self):
        if not self._hit:

            next_coord = self._calc_next_move(self._target_coord)

            self._world_coord = next_coord

            if self._world_coord.calculate_distance(self._target_coord) < self._radius:
                self._hit = True

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

    def _check_targets_hit(self):
        if self._hit:
            for npc in self._npc_list:
                npc_coord = npc.get_coord()
                distance_from_projectile = npc_coord.calculate_distance(self._world_coord.get_coord())

                if distance_from_projectile <= self._radius:
                    npc.kill()

    def has_hit(self):
        return self._hit


class Bullet(Projectile):
    def __init__(self, start_coord, target_coord, speed, npc_list):
        super().__init__(start_coord, target_coord, speed, npc_list)

    def _check_targets_hit(self):
        pass


class Shell(Projectile):
    def __init__(self, start_coord, target_coord, speed, blast_factor, npc_list):
        super().__init__(start_coord, target_coord, speed, npc_list)

        self._blast_radius = self._radius * blast_factor
        self._debug = True
        self._exploded = False

        self._explosion_sound = pygame.mixer.Sound("assets/audio/artillery_explosion.wav")
        self._incoming_sound = pygame.mixer.Sound("assets/audio/incoming_explosion.wav")
        self._timer = Timer()

    def draw(self, screen, camera):
        super().draw(screen, camera)

        if self._debug and self.has_hit():

            screen_coord = camera.translate_coord(self._world_coord.get_coord())

            pygame.draw.circle(screen, self._colour, screen_coord,
                               self._blast_radius, width=4)

    def update(self):
        super().update()

        self._execute_incoming_sound()

    def _check_targets_hit(self):
        self._execute_incoming_sound()

        if self._hit:
            for npc in self._npc_list:
                npc_coord = npc.get_coord()
                distance_from_blast = npc_coord.calculate_distance(self._world_coord.get_coord())

                if distance_from_blast <= self._blast_radius:
                    npc.kill()

            if self._timer.is_finished(self._incoming_sound.get_length() * 1.5):
                self._explosion_sound.play()

            if self._timer.is_finished(self._explosion_sound.get_length() * 7):
                self._exploded = True

    def _execute_incoming_sound(self):
        distance_from_explosion = self._world_coord.calculate_distance(self._target_coord)

        if (self._blast_radius < distance_from_explosion < self._blast_radius * 2
                and not self._mute_sounds):
            self._incoming_sound.play()

    def get_sounds(self):
        return self._incoming_sound, self._explosion_sound

    def has_exploded(self):
        return self._exploded

    def set_mute_sounds(self, mute_sounds):
        self._mute_sounds = mute_sounds
