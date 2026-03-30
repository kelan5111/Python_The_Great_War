import pygame
import random

from game_mechanics import Actor, Timer
from sprite_resources import SpriteSheet


class Particle:
    def __init__(self, speed, lifetime, width, height, max_frame, sprite_sheet=None, angle=None):

        self._speed = speed
        self._lifetime = lifetime
        self._rotation = angle

        self._sprite_sheet = None
        self._animation = []
        self._frame = 0
        self._max_frame = max_frame
        self._curr_img = None
        self._animation_cooldown = 1
        self._animation_timer = Timer()

        if sprite_sheet is not None:
            self._build_animation()

    def draw(self, screen, screen_coord):
        img_rect = self._curr_img.get_rect()

        screen.blit(self._curr_img, screen_coord)

        if self._frame < 16:
            self._frame += 1

    def act(self, mouse_pos):
        self._update_sprite()

    def _update_sprite(self):
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

        self._rotate()

    def get_frame(self):
        return self._frame


class Smoke(Particle):

    SPRITE_SHEET = "assets/images/sprite_sheets/artillery_smoke-Sheet.png"

    def __init__(self, speed, lifetime, width, height, max_frame):
        super().__init__(speed, lifetime, width, height, max_frame, sprite_sheet=None, angle=None)

        self._sprite_sheet = Smoke.SPRITE_SHEET
