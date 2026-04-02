import pygame
from battlefield import Battlefield


class Game:
    def __init__(self, width, height, player_country):
        self._width = width
        self._height = height
        self._screen = pygame.display.set_mode((width, height), pygame.FULLSCREEN, vsync=1)
        self._running = True

        self._dt = 0.0

        self._battlefield = Battlefield(self._screen, width, height, player_country)

    def run(self):
        clock = pygame.time.Clock()

        while self._running:
            raw_mouse_pos = pygame.mouse.get_pos()
            self._dt = clock.tick(60) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._running = False

                self._manage_input(event, raw_mouse_pos)

            self._act(raw_mouse_pos)
            self._draw()

            pygame.display.flip()
            clock.tick(60)

        pygame.quit()

    def _draw(self):
        self._battlefield.draw()

    def _act(self, raw_mouse_pos):
        self._battlefield.act(raw_mouse_pos, self._dt)

    def _manage_input(self, event, mouse_pos):
        self._battlefield.manage_input(event, mouse_pos)
