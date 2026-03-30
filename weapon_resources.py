import enum

import pygame
import random
from abc import ABC, abstractmethod

from coordinate import Coordinate
from npc import FightingDirection
from sprite_resources import SpriteSheet
from game_mechanics import Actor, Timer


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
        self._update_projectile(screen, camera)

    def act(self, *args):
        self._update_rect()

    @abstractmethod
    def shoot(self, target_coord, npc_list):
        pass

    @abstractmethod
    def reload(self, *args):
        pass

    def _update_rect(self):
        self._rect = pygame.Rect(self._world_coord.get_coord(), (self._width, self._height))

    @abstractmethod
    def _update_projectile(self, screen, camera):
        for p in self._active_projectile:
            p.update(screen, camera)

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
        self._fighting_direction = country.value["fighting_direction"]

        self._friendly_slt_coord = friendly_slt_coord
        self._enemy_slt_coord = enemy_slt_coord
        self._friendly_flt_coord = friendly_flt_coord
        self._enemy_flt_coord = enemy_flt_coord

        self._max_gunner = 6
        self._timer = Timer()
        self._gunners = []
        self._barrage_coord = None

    def draw(self, screen, camera):
        screen_rect = camera.translate_rect(self._rect)
        pygame.draw.rect(screen, self._colour, screen_rect)

        self._update_projectile(screen, camera)

    def shoot(self, target_coord, npc_list):
        if len(self._gunners) > 0 and self._shell_supply > 0:
            start_x = self._world_coord.get_x()
            start_y = self._world_coord.get_y()

            shell = Shell(Coordinate(start_x, start_y), target_coord, speed=5, blast_factor=5, npc_list=npc_list)

            shell.set_curr_state(ShellState.SHOT)

            self._active_projectile.append(shell)
            self._shell_supply -= 1

    def shoot_random_projectile(self, npc_list):
        if len(self._gunners) > 0:
            if not self._timer.is_started():
                self._timer.start()

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

    def _update_projectile(self, screen, camera):
        super()._update_projectile(screen, camera)

        for shell in self._active_projectile:
            if shell.has_exploded():
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

    def _update_projectile(self, screen, camera):
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
        self._alive = True
        self._targets_hit = []

    def update(self, screen, screen_coord):
        if self._alive:
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

    @abstractmethod
    def _check_targets_hit(self):
        pass

    @abstractmethod
    def _check_targets_miss(self, npc, distance_from_projectile):
        pass

    def has_hit(self):
        return self._hit


class Bullet(Projectile):
    def __init__(self, start_coord, target_coord, speed, npc_list):
        super().__init__(start_coord, target_coord, speed, npc_list)

    def draw(self, screen, camera):
        pass

    def _check_targets_hit(self):
        pass

    def _check_targets_miss(self, npc, distance_from_projectile):
        pass


class Shell(Projectile):
    HIGH_FACTOR_BLAST = 8
    MID_FACTOR_BLAST = 4
    LOW_FACTOR_BLAST = 2

    def __init__(self, start_coord, target_coord, speed, blast_factor, npc_list):
        super().__init__(start_coord, target_coord, speed, npc_list)

        self._blast_radius = self._radius * blast_factor

        self._played_incoming_sound = False
        self._played_explosion_sound = False

        self._curr_state = ShellState.INACTIVE
        self._distance_from_player = None

        self._sprite_sheet = SpriteSheet("assets/images/sprite_sheets/artillery_smoke-Sheet.png")
        self._smoke_animation = []
        self._animation_cooldown = 1
        self._animation_timer = Timer()
        self._frame = 0
        self._nearby_soldiers = []

        self._explosion_sound = pygame.mixer.Sound("assets/audio/artillery_explosion.wav")
        self._incoming_sound = pygame.mixer.Sound("assets/audio/incoming_explosion.wav")
        self._timer = Timer()

        self._build_animations()

    def _draw_smoke_animation(self, screen, screen_coord):
        img = self._smoke_animation[self._frame]

        img_rect = img.get_rect()
        img_rect.center = screen_coord
        screen.blit(img, img_rect)

        if self._frame < 16:
            self._frame += 1

    def _rotate_smoke_images(self):
        rand_dir = random.randint(0, 1)
        rand_angle = 0

        if rand_dir == 0:
            rand_angle = random.randint(0, 20)
        elif rand_dir == 1:
            rand_angle = random.randint(-20, 0)

        for frame in range(len(self._smoke_animation)):
            self._smoke_animation[frame] = pygame.transform.rotate(
                self._smoke_animation[frame], rand_angle
            ).convert_alpha()

    def _build_animations(self):
        scale = 3

        self._smoke_animation = self._sprite_sheet.get_sprite_list(
            1, 17, 64,
            64, scale, (0, 0, 0)
        )

        self._rotate_smoke_images()

    def update(self, screen, camera):
        super().update(screen, camera)

        self._distance_from_player = self._world_coord.calculate_distance(self._target_coord)

        self._monitor_events(screen, camera)

    def _move(self):
        if self._curr_state == ShellState.SHOT or self._curr_state == ShellState.INCOMING:
            next_coord = self._calc_next_move(self._target_coord)
            self._world_coord = next_coord

    def _monitor_events(self, screen, camera):
        screen_coord = camera.translate_coord(self._world_coord.get_coord())

        self._monitor_shot(screen, screen_coord)
        self._monitor_incoming_blast(screen, screen_coord)
        self._monitor_hit(screen, screen_coord)
        self._monitor_explosion(screen, screen_coord)

    def _monitor_shot(self, screen, screen_coord):
        if self._curr_state == ShellState.SHOT:
            pygame.draw.circle(screen, self._colour, screen_coord, self._radius)

            incoming_sound_length = self._incoming_sound.get_length()

            if self._radius < self._distance_from_player < self._blast_radius * Shell.HIGH_FACTOR_BLAST:
                self._curr_state = ShellState.INCOMING

    def _monitor_incoming_blast(self, screen, screen_coord):
        if self._curr_state == ShellState.INCOMING:
            self._check_soldier_nearby()

            incoming_sound_length = self._incoming_sound.get_length()
            # Draw the shell circle
            pygame.draw.circle(screen, self._colour, screen_coord, self._radius)

            if (len(self._nearby_soldiers) > 0 and
                    not self._played_incoming_sound):
                self._incoming_sound.play()
                self._played_incoming_sound = True

            if self._distance_from_player < self._radius:
                self._curr_state = ShellState.HIT

    def _check_soldier_nearby(self):
        for soldier in self._npc_list:
            soldier_coord = soldier.get_coord()
            distance_from_target = soldier_coord.calculate_distance(self._target_coord)

            if distance_from_target < self._blast_radius * 4:
                self._nearby_soldiers.append(soldier)

    def _monitor_hit(self, screen, screen_coord):
        if self._curr_state == ShellState.HIT:
            self._incoming_blast = False

            self._draw_smoke_animation(screen, screen_coord)

            if not self._played_explosion_sound:
                self._calc_shell_shock()
                self._check_npc_deaths()

                self._explosion_sound.play()
                self._played_explosion_sound = True

            if self._frame >= 16:
                if self._sleep_cooldown(1.5):
                    self._frame = 0

                    self._curr_state = ShellState.EXPLODED

    def _monitor_explosion(self, screen, screen_coord):
        if self._curr_state == ShellState.EXPLODED:
            self._curr_state = ShellState.INACTIVE
            self._alive = False

    def _check_npc_deaths(self):
        if len(self._nearby_soldiers) > 0:
            for s in self._nearby_soldiers:
                s_coord = s.get_coord()
                distance_from_explosion = s_coord.calculate_distance(self._target_coord)

                if distance_from_explosion < self._blast_radius:
                    s.kill()

    def _calc_shell_shock(self):
        for npc in self._npc_list:
            if npc.is_alive():
                npc_coord = npc.get_coord()
                distance_from_blast = (npc_coord.calculate_distance(self._target_coord))
                new_moral = npc.get_morale()

                if distance_from_blast <= self._blast_radius * Shell.HIGH_FACTOR_BLAST:
                    new_moral -= MoraleLoss.HIGH.value

                elif distance_from_blast <= self._blast_radius * Shell.MID_FACTOR_BLAST:
                    new_moral -= MoraleLoss.MEDIUM.value

                elif distance_from_blast <= self._blast_radius * Shell.LOW_FACTOR_BLAST:
                    new_moral -= MoraleLoss.LOW.value

                npc.set_shell_shocked(True)
                npc.set_morale(new_moral)

    def _sleep_cooldown(self, secs):
        if not self._timer.is_started():
            self._timer.start()

        if self._timer.is_finished(secs):
            self._timer.reset()
            return True

        return False

    def get_sounds(self):
        return self._incoming_sound, self._explosion_sound

    def has_exploded(self):
        return self._curr_state == ShellState.EXPLODED

    def set_mute_sounds(self, mute_sounds):
        self._mute_sounds = mute_sounds

    def set_curr_state(self, curr_state):
        self._curr_state = curr_state


class MoraleLoss(enum.Enum):
    LOW = 2
    MEDIUM = 4
    HIGH = 6


class ShellState(enum.Enum):
    INACTIVE = 0
    SHOT = 1
    INCOMING = 2
    HIT = 3
    EXPLODED = 4
