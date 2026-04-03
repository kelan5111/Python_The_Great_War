import pygame


class SpriteSheet:
    def __init__(self, image_path):

        self._sprite_sheet = pygame.image.load(image_path)

    def get_sprite_list(self, num_col, num_row, frame_width, frame_height, scale, background_colour):
        sprite_images = []

        for y in range(num_col):
            col = y * frame_width
            row = 0
            for x in range(num_row):
                row = x * frame_height

                image = pygame.Surface((frame_width, frame_height)).convert_alpha()

                image.blit(self._sprite_sheet, (0, 0), (row, col, frame_width, frame_height))

                image = pygame.transform.scale(image, (frame_width * scale, frame_height * scale))
                image.set_colorkey(background_colour)

                sprite_images.append(image)

        return sprite_images
