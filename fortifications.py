import pygame

from game_mechanics import Actor


class Fortifications(Actor):
    def __init__(self, image_path, rotate_angle, coord, width, height, group, protection_factor):
        super().__init__(coord, width, height, group)

        self._image = pygame.transform.scale(pygame.image.load(image_path), (width, height))

        if rotate_angle > 0:
            self._image = pygame.transform.rotate(self._image, rotate_angle)

        self._rect = self._image.get_rect()

        self._protection_factor = protection_factor
        self._health = 100

    def draw(self, screen, camera):
        screen_rect = camera.translate_rect(self._rect)
        screen.blit(self._image, screen_rect)

    def act(self, mouse_pos):
        self._update_rect()

    def _update_rect(self):
        self._rect.center = self._world_coord.get_coord()
        self._rect.width = self._width
        self._rect.height = self._height


class Sandbag(Fortifications):
    IMAGE_PATH = "assets/images/sandbag_normal.png"

    def __init__(self, image_path, rotate, coord, width, height, group, protection_factor):
        super().__init__(image_path, rotate, coord, width, height, group, protection_factor)
