import pygame
import random

from game_mechanics import Actor, Timer
from sprite_resources import SpriteSheet


class Particle:
    def __init__(self, speed, lifetime, width, height, max_frame, animation_cooldown, sprite_sheet=None, angle=None):

        self._speed = speed
        self._lifetime = lifetime
        self._alpha = 255
        self._lifetime_timer = Timer()
        self._rotation = angle

        self._sprite_sheet = None
        self._animation = []
        self._frame = 0
        self._max_frame = max_frame
        self._curr_img = None
        self._animation_cooldown = animation_cooldown
        self._animation_timer = Timer()

    def draw(self, screen, screen_coord):
        if self._curr_img is None:
            return

        img_rect = self._curr_img.get_rect()

        screen.blit(self._curr_img, screen_coord)

        if self._animated_cooldown():
            if self._frame < self._max_frame:
                self._frame += 1

    def update(self):
        self._update_sprite()

    def _update_sprite(self):
        if len(self._animation) > 0:
            self._curr_img = self._animation[self._frame]

    def _rotate(self):
        self._curr_img = pygame.transform.rotate(self._curr_img, self._rotation).convert_alpha()

    def set_rand_rotation(self):
        rand_dir = random.randint(0, 1)
        rand_angle = 0

        if rand_dir == 0:
            rand_angle = random.randint(0, 20)
        elif rand_dir == 1:
            rand_angle = random.randint(-20, 0)

        self._rotation = rand_angle

    def _build_animation(self):
        scale = 3

        self._animation = self._sprite_sheet.get_sprite_list(
            1, 17, 64,
            64, scale, (0, 0, 0)
        )

        if self._rotation is not None:
            self._rotate()

    def _animated_cooldown(self):
        if not self._animation_timer.is_started():
            self._animation_timer.start()

        if self._animation_timer.is_finished(self._animation_cooldown):
            self._animation_timer.reset()
            return True

        return False

    def start_fading(self):
        if self._alpha > 0:
            self._alpha -= 50

        self._curr_img.set_alpha(self._alpha)

    def get_frame(self):
        return self._frame

    def get_alpha(self):
        return self._alpha


class Smoke(Particle):

    SPRITE_SHEET = "assets/images/sprite_sheets/artillery_smoke-Sheet.png"

    def __init__(self, speed, lifetime, width, height, max_frame, animation_cooldown):
        super().__init__(speed, lifetime, width, height, max_frame, animation_cooldown, sprite_sheet=None, angle=None)

        self._sprite_sheet = SpriteSheet(Smoke.SPRITE_SHEET)
        self._build_animation()
