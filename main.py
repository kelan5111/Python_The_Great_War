from game import Game
from npc import Country
import pygame


def calc_screen_resolution():
    width, height = pygame.display.get_desktop_sizes()[0]

    return width, height


def main():
    pygame.init()
    pygame.font.init()
    pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)

    width, height = calc_screen_resolution()

    game = Game(width, height, Country.BRITAIN)

    # Running game
    game.run()


if __name__ == "__main__":
    main()
