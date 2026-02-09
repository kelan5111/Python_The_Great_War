import pygame
import random

from waypoint import Graph
from coordinate import Coordinate
from npc import Soldier, Country, Weapon
from trench import FrontLineTrench, SupportTrench


class Game:
    def __init__(self):
        self.__soldiers = []
        self.__other_objects = []
        self.__countries = [Country.GERMANY, Country.BRITAIN]

        self.__width = 1280
        self.__height = 720
        self.__screen = pygame.display.set_mode((self.__width, self.__height))

        self.__running = True

        self.__waypoint_graph = Graph(self.__width, self.__height)

    def run(self):
        clock = pygame.time.Clock()

        self.__initialize()

        while self.__running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.__running = False

                self.__manage_input(event)

            self.__draw()
            self.__update()

            pygame.display.flip()
            clock.tick(60)

        pygame.quit()

    def __initialize(self):
        self.__waypoint_graph.build_waypoints()

        # Starting pos for npc
        num_soldiers = 10

        # Creating soldiers and placing them at random positions
        for i in range(num_soldiers):
            rand_x = random.randint(0, self.__width)
            rand_y = random.randint(0, self.__height)
            starting_waypoint = self.__waypoint_graph.find_nearest_waypoint(Coordinate(rand_x, rand_y))

            soldier = Soldier(starting_waypoint, self.__countries[random.randint(0, 1)])
            weapon = Weapon("none", soldier)
            soldier.arm_with_weapon(weapon)

            self.__add_soldier(soldier)
            self.__add_others(weapon)

    def __draw(self):
        self.__screen.fill((48, 35, 9))

        self.__waypoint_graph.draw(self.__screen)

        # Draw soldiers
        for soldier in self.__soldiers:
            soldier.draw(self.__screen)

        # Draw other objects
        for other in self.__other_objects:
            other.draw(self.__screen)

    def __update(self):
        for soldier in self.__soldiers:
            soldier.update(self.__soldiers)

            self.__manage_death(soldier)

        for other in self.__other_objects:
            other.update()

    def __manage_input(self, event):
        mouse_pos = pygame.mouse.get_pos()

        if event.type == pygame.MOUSEBUTTONUP:
            if pygame.mouse.get_pressed() and event.button == 1:
                for soldier in self.__soldiers:
                    # Selecting a soldier
                    if soldier.is_selected(mouse_pos):
                        soldier.select()
                    else:
                        soldier.unselect()

            if pygame.mouse.get_pressed() and event.button == 3:
                for soldier in self.__soldiers:
                    if soldier.has_selected():
                        soldier.set_path(self.__waypoint_graph, mouse_pos)
                        soldier.unselect()

    def __add_soldier(self, soldier):
        self.__soldiers.append(soldier)

    def __remove_soldier(self, soldier):
        self.__soldiers.remove(soldier)

    def __add_others(self, o):
        self.__other_objects.append(o)

    def __remove_others(self, o):
        self.__other_objects.remove(o)

    def __manage_death(self, soldier):
        if not soldier.is_alive():
            weapon = soldier.get_weapon()
            self.__other_objects.remove(weapon)

            self.__soldiers.remove(soldier)
