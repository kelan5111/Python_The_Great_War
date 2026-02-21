import pygame
import random
import json

from waypoint import Graph
from coordinate import Coordinate
from npc import Soldier, Country, Weapon
from game_mechanics import Group, Actor
from game_gui import SelectBox, Button, InteractiveTab, Console
from trench import FrontLineTrench, SupportTrench, Trench


class Game:
    def __init__(self, width, height, player_country):
        self.__countries = [Country.GERMANY, Country.BRITAIN]
        self.__player = player_country
        self.__player_num = random.randint(0, 2)

        self.__width = width
        self.__height = height
        self.__screen = pygame.display.set_mode((self.__width, self.__height), pygame.FULLSCREEN)
        self.__ground_colour = (48, 35, 9)

        self.__running = True

        self.__group = Group(self.__screen)
        self.__field_waypoints = Graph(self.__width, self.__height, 30)

        self.__select_box = SelectBox(player_country)
        self.__interactive_tab = InteractiveTab(self.__width)
        self.__debug_console = Console(Coordinate(0, self.__height - 40), self.__width, 40, (0, 0, 0), '> ')

    def run(self):
        clock = pygame.time.Clock()

        self.__initialize_objects()
        self.__initialize_waypoints()

        while self.__running:
            mouse_pos = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.__running = False

                self.__manage_input(event)

            self.__draw_world()

            self.__group.draw()
            self.__group.act(mouse_pos)

            self.__interactive_tab.draw(self.__screen)
            self.__interactive_tab.update()

            self.__debug_console.draw(self.__screen)
            self.__debug_console.update()

            pygame.display.flip()
            clock.tick(60)

        pygame.quit()

    def __initialize_objects(self):
        pygame.display.set_caption('The Great War')

        actors = self.__group.get_actors()

        button_one = Button((255, 0, 0), (255, 255, 255), "Button One", 0, (0, 0, 0))
        self.__interactive_tab.add_icon(button_one)

        front_line_one = FrontLineTrench(Coordinate(150, 0), 50, self.__height, 10, self.__player, self.__ground_colour,
                                         actors)
        support_line_one = SupportTrench(Coordinate(50, 0), 50, self.__height, 50, self.__player, self.__ground_colour,
                                         actors)
        front_line_two = FrontLineTrench(Coordinate(self.__width - 200, 0), 50, self.__height, 10, Country.GERMANY,
                                         self.__ground_colour, actors)
        support_line_two = SupportTrench(Coordinate(self.__width - 100, 0), 50, self.__height, 50, Country.GERMANY,
                                         self.__ground_colour, actors)

        trench_spawn = [support_line_one.get_proximity(), support_line_two.get_proximity()]
        starting_trenches = [support_line_one, support_line_two]

        self.__group.add(front_line_one)
        self.__group.add(support_line_one)
        self.__group.add(front_line_two)
        self.__group.add(support_line_two)

        self.__initialize_soldiers(10, trench_spawn, starting_trenches)

        self.__group.add(self.__select_box)

    def __initialize_waypoints(self):
        self.__field_waypoints.build()
        self.__field_waypoints.draw(self.__screen)

    def __draw_world(self):
        self.__screen.fill(self.__ground_colour)

    def __manage_input(self, event):
        self.__manage_mouse_input(event)
        self.__manage_key_input(event)

    def __manage_mouse_input(self, event):
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

                for section in self.__interactive_tab.get_sections():
                    if isinstance(section, Button):
                        section.set_select(False)

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

                for section in self.__interactive_tab.get_sections():
                    if section.has_collided(mouse_pos):
                        if isinstance(section, Button):
                            section.set_select(True)

                # If a text box is selected
                if self.__debug_console.has_collided(mouse_pos):
                    self.__debug_console.set_active(True)

            # Select Trench
            if event.button == 3:
                for actor in self.__group.get_actors():
                    if isinstance(actor, Trench) and actor.get_country() == self.__player:
                        if actor.has_hover():
                            actor.set_select(True)

    def __manage_key_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSLASH:
                if self.__debug_console.is_shown():
                    self.__debug_console.set_show(False)
                    self.__debug_console.set_active(False)
                else:
                    self.__debug_console.set_show(True)

            # Managing the consoles text input
            elif self.__debug_console.is_active():
                if event.key == pygame.K_RETURN:
                    self.__debug_console.clear_text()
                elif event.key == pygame.K_BACKSPACE:
                    self.__debug_console.remove_unicode()
                else:
                    self.__debug_console.insert_unicode(event.unicode)

    def __initialize_soldiers(self, num_soldiers, trench_coord_list, starting_trenches):
        for sides in range(0, 2):
            for soldier_count in range(num_soldiers):
                starting_trench = starting_trenches[sides]
                starting_trench_coord = trench_coord_list[sides]

                rand_x = random.randint(starting_trench_coord[0][0], starting_trench_coord[0][1])
                rand_y = random.randint(starting_trench_coord[1][0], starting_trench_coord[1][1])

                trench_waypoint_graph = starting_trench.get_waypoint_graph()
                weapon = Weapon("none")

                soldier = Soldier(Coordinate(rand_x, rand_y), 20, 20, trench_waypoint_graph, self.__countries[sides],
                                  self.__group.get_actors(), weapon)

                self.__group.add(soldier)
                self.__group.add(weapon)
