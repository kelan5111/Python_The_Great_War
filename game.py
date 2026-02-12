import pygame
import random

from waypoint import Graph
from coordinate import Coordinate
from npc import Soldier, Country, Weapon
from game_mechanics import SelectBox, Group, JSONLoader
from trench import FrontLineTrench, SupportTrench


class Game:
    def __init__(self, player_country):
        self.__countries = [Country.GERMANY, Country.BRITAIN]
        self.__player = player_country

        self.__width = 1280
        self.__height = 720
        self.__screen = pygame.display.set_mode((self.__width, self.__height))
        self.__ground_colour = (48, 35, 9)

        self.__running = True

        self.__group = Group(self.__screen)
        self.__field_waypoints = Graph(self.__width, self.__height, 30)
        self.__select_box = SelectBox(player_country)

    def run(self):
        clock = pygame.time.Clock()

        self.__initialize()
        #self.__world_waypoints.debug_game()

        while self.__running:
            mouse_pos = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.__running = False

                self.__manage_input(event)

            self.__draw_world()

            self.__group.draw()
            self.__group.act()

            self.__field_waypoints.draw(self.__screen)
            self.__select_box.execute(mouse_pos)

            pygame.display.flip()
            clock.tick(60)

        pygame.quit()

    def __initialize(self):
        actors = self.__group.get_actors()

        front_line_one = FrontLineTrench(50, self.__height, 10, Coordinate(150, 0), self.__player, self.__ground_colour, actors)
        support_line_one = SupportTrench(50, self.__height, 50, Coordinate(50, 0), self.__player, self.__ground_colour, actors)
        front_line_two = FrontLineTrench(50, self.__height, 10, Coordinate(self.__width - 200, 0), Country.GERMANY, self.__ground_colour, actors)
        support_line_two = SupportTrench(50, self.__height, 50, Coordinate(self.__width - 100, 0), Country.GERMANY, self.__ground_colour, actors)

        self.__field_waypoints.build()
        #self.__field_waypoints.debug_game()

        self.__group.add(front_line_one)
        self.__group.add(support_line_one)
        self.__group.add(front_line_two)
        self.__group.add(support_line_two)

        num_soldiers = 10
        # Creating soldiers and placing them at random positions
        for i in range(num_soldiers):
            rand_x = random.randint(0, self.__width)
            rand_y = random.randint(0, self.__height)
            starting_waypoint = self.__field_waypoints.find_nearest_waypoint(Coordinate(rand_x, rand_y))

            weapon = Weapon("none")
            soldier = Soldier(starting_waypoint, self.__countries[random.randint(0, 1)], actors, weapon)
            self.__group.add(soldier)
            self.__group.add(weapon)

        self.__group.add(self.__select_box)

    def __draw_world(self):
        self.__screen.fill(self.__ground_colour)

    def __manage_input(self, event):
        mouse_pos = pygame.mouse.get_pos()

        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:

                # If we are dragging a select box
                if self.__select_box.is_pressed():
                    self.__select_box.end_drag(self.__group.get_actors())

                # If we are selecting a soldier manually on screen
                for actor in self.__group.get_actors():
                    if isinstance(actor, Soldier):
                        if (actor.get_country() == self.__player and
                                actor.has_collided(mouse_pos)):
                            actor.select()

            # Any soldier is selected they will move to mouse pos
            if event.button == 3:
                for actor in self.__group.get_actors():
                    if isinstance(actor, Soldier):
                        actor.set_path(self.__field_waypoints, mouse_pos)
                        actor.deselect()

        if event.type == pygame.MOUSEBUTTONDOWN:
            # If we click and hold then select box
            if event.button == 1:
                self.__select_box.pressed(mouse_pos)
