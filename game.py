import pygame
import random
import json

from waypoint import Graph
from coordinate import Coordinate
from npc import Soldier, Country, Weapon
from game_mechanics import SelectBox, Group, Button
from trench import FrontLineTrench, SupportTrench, Trench


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
        pygame.font.init()

        self.__initialize()

        while self.__running:
            mouse_pos = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.__running = False

                self.__manage_input(event)

            self.__draw_world()

            self.__group.draw()
            self.__group.act(mouse_pos)

            self.__field_waypoints.draw(self.__screen)

            pygame.display.flip()
            clock.tick(60)

        pygame.quit()

    def __initialize(self):
        pygame.display.set_caption('The Great War')

        actors = self.__group.get_actors()

        front_line_one = FrontLineTrench(Coordinate(150, 0), 50, self.__height, 10, self.__player, self.__ground_colour,
                                         actors)
        support_line_one = SupportTrench(Coordinate(50, 0), 50, self.__height, 50, self.__player, self.__ground_colour,
                                         actors)
        front_line_two = FrontLineTrench(Coordinate(self.__width - 200, 0), 50, self.__height, 10, Country.GERMANY,
                                         self.__ground_colour, actors)
        support_line_two = SupportTrench(Coordinate(self.__width - 100, 0), 50, self.__height, 50, Country.GERMANY,
                                         self.__ground_colour, actors)

        trench_spawn = [front_line_one.get_proximity(), front_line_two.get_proximity()]
        starting_trenches = [support_line_one, support_line_two]

        # Buttons
        button = Button(Coordinate(500, 100), 400, 400, (255, 0, 0), (255, 255, 255), "Button", 10, (0, 0, 0))

        self.__field_waypoints.build()

        self.__group.add(front_line_one)
        self.__group.add(support_line_one)
        self.__group.add(front_line_two)
        self.__group.add(support_line_two)
        self.__group.add(button)

        self.__spawn_soldier(None, 10, trench_spawn, starting_trenches)

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

                # If we are selecting a type from collision_options manually on screen
                for actor in self.__group.get_actors():
                    if isinstance(actor, Soldier):
                        if (actor.get_country() == self.__player and
                                actor.has_collided(mouse_pos)):
                            actor.set_select(True)

                    elif isinstance(actor, Button):
                        actor.set_select(False)

            # Any soldier is selected they will move to mouse pos
            if event.button == 3:
                for actor in self.__group.get_actors():
                    if isinstance(actor, Soldier):
                        if actor.has_selected() and not actor.is_idle():
                            actor.set_path(mouse_pos)
                            actor.set_select(False)

                            options = (trench for trench in self.__group.find(Trench) if trench.has_hover())
                            selected_trench = next(options, None)

                            if selected_trench is not None:
                                # Change the waypoint graph of the soldier to the trench's
                                actor.set_next_waypoint_graph(selected_trench.get_waypoint_graph())
                                actor.set_idle(True)

                    # Unselect Trench once selected
                    elif isinstance(actor, Trench):
                        if actor.has_hover():
                            actor.set_select(False)

        if event.type == pygame.MOUSEBUTTONDOWN:
            # If we click and hold then select box
            if event.button == 1:
                self.__select_box.pressed(mouse_pos)

                for actor in self.__group.get_actors():
                    if isinstance(actor, Button) and actor.has_collided(mouse_pos):
                        actor.set_select(True)

            # Select Trench
            if event.button == 3:
                for actor in self.__group.get_actors():
                    if isinstance(actor, Trench) and actor.get_country() == self.__player:
                        if actor.has_hover():
                            actor.set_select(True)

    def __spawn_soldier(self, country, num_soldiers, trench_coord_list, starting_trenches):
        for soldier_count in range(num_soldiers):
            trench_coord = random.choice(trench_coord_list)
            trench = random.choice(starting_trenches)

            rand_x = random.randint(trench_coord[0][0], trench_coord[0][1])
            rand_y = random.randint(trench_coord[1][0], trench_coord[1][1])

            trench_waypoint_graph = trench.get_waypoint_graph()

            starting_waypoint = trench_waypoint_graph.find_nearest_waypoint(Coordinate(rand_x, rand_y))
            random_country = random.choice(self.__countries)
            weapon = Weapon("none")

            soldier = Soldier(Coordinate(rand_x, rand_y), 20, 20, trench_waypoint_graph, random_country, self.__group.get_actors(), weapon)

            self.__group.add(soldier)
            self.__group.add(weapon)
