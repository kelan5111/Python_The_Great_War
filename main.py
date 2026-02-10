from game import Game
from npc import Country


def main():
    game = Game(Country.BRITAIN)

    # Running game
    game.run()


if __name__ == "__main__":
    main()
