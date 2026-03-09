import pygame
import random

from waypoint import Graph
from coordinate import Coordinate, Direction
from npc import Soldier, Country, Gun, Artillery
from game_mechanics import Group, Timer, Camera
from game_gui import SelectBox, Button, InteractiveTab, Console
from trench import FrontLineTrench, SupportTrench, Trench


class Game:
    def __init__(self, width, height, player_country):
        self.__countries = [Country.GERMANY, Country.BRITAIN]
        self.__player = player_country
        self.__player_num = random.randint(0, 2)

        self.__width = width
        self.__height = height
        self.__screen = pygame.display.set_mode((width, height), pygame.FULLSCREEN, vsync=1)
        self.__dt = 0.0

        self.__world_camera = Camera(self.__width, self.__height)

        self.__width = width
        self.__height = height
        self.__ground_colour = (48, 35, 9)

        self.__running = True

        self.__group = Group(self.__screen)
        self.__field_waypoints = Graph(self.__width + (self.__width // 2), self.__height, 30)

        self.__select_box = SelectBox(player_country, 0, 0, self.__group)
        self.__timer = Timer()
        self.__interactive_tab = InteractiveTab(self.__width)
        self.__debug_console = None

    def run(self):
        clock = pygame.time.Clock()

        self.__initialize_objects()
        self.__initialize_waypoints()

        while self.__running:
            world_mouse_pos = pygame.mouse.get_pos()
            screen_mouse_pos = self.__world_camera.translate_mouse_pos(world_mouse_pos)
            self.__dt = clock.tick(60) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.__running = False

                self.__manage_input(event, screen_mouse_pos)

            self.__update(screen_mouse_pos)
            self.__manage_camera_input()
            self.__draw()

            pygame.display.flip()
            clock.tick(60)

        pygame.quit()

    def __draw(self):
        self.__screen.fill(self.__ground_colour)
        self.__group.draw(self.__world_camera)
        self.__field_waypoints.draw(self.__screen, self.__world_camera)
        self.__interactive_tab.draw(self.__screen, self.__world_camera)
        self.__debug_console.draw(self.__screen, self.__world_camera)

    def __update(self, mouse_pos):
        self.__group.act(mouse_pos)
        self.__interactive_tab.update()
        self.__debug_console.update()

    def __initialize_objects(self):
        pygame.display.set_caption('The Great War')

        button_one = Button((255, 0, 0), (255, 255, 255), "Button One", 0, (0, 0, 0))
        self.__interactive_tab.add_icon(button_one)

        front_line_one = FrontLineTrench(Coordinate(150, 0), 50, self.__height, 10, self.__player, self.__ground_colour,
                                         self.__group)
        support_line_one = SupportTrench(Coordinate(50, 0), 50, self.__height, 50, self.__player, self.__ground_colour,
                                         self.__group)
        front_line_two = FrontLineTrench(Coordinate(self.__width - 200, 0), 50, self.__height, 10, Country.GERMANY,
                                         self.__ground_colour, self.__group)
        support_line_two = SupportTrench(Coordinate(self.__width - 100, 0), 50, self.__height, 50, Country.GERMANY,
                                         self.__ground_colour, self.__group)

        support_line_trenches_proximity = [support_line_one.get_proximity(), support_line_two.get_proximity()]
        front_line_trenches_proximity = [support_line_one, support_line_two]

        self.__debug_console = Console(Coordinate(0, self.__height - 40), self.__width, 200, (0, 0, 0),
                                       '[CONSOLE]', self.__field_waypoints,
                                       [front_line_one, support_line_one, front_line_two, support_line_two])

        self.__initialize_soldiers(10, support_line_trenches_proximity, front_line_trenches_proximity)
        self.__initialize_artillery(support_line_trenches_proximity)

    def __initialize_waypoints(self):
        self.__field_waypoints.build()
        self.__field_waypoints.draw(self.__screen, self.__world_camera)

    def __manage_input(self, event, mouse_pos):
        self.__manage_mouse_input(event, mouse_pos)
        self.__manage_key_input(event)

    def __manage_mouse_input(self, event, mouse_pos):

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
                else:
                    self.__debug_console.set_active(False)

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
                else:
                    self.__debug_console.set_active(True)
                    self.__debug_console.set_show(True)

            elif self.__debug_console.is_active():
                # Managing the consoles text input
                if event.key == pygame.K_RETURN:
                    self.__debug_console.execute_command()

                elif event.key == pygame.K_BACKSPACE:
                    self.__debug_console.remove_char()
                else:
                    self.__debug_console.insert_char(event.unicode)

    def __manage_camera_input(self):
        keys = pygame.key.get_pressed()

        # Manage the movement of the camera
        if keys[pygame.K_d]:
            self.__world_camera.update(Direction.RIGHT, self.__dt)
        elif keys[pygame.K_a]:
            self.__world_camera.update(Direction.LEFT, self.__dt)

    def __initialize_soldiers(self, num_soldiers, trench_coord_list, starting_trenches):
        for sides in range(0, 2):
            for soldier_count in range(num_soldiers):
                starting_trench = starting_trenches[sides]
                starting_trench_coord = trench_coord_list[sides]

                rand_x = random.randint(starting_trench_coord[0][0], starting_trench_coord[0][1])
                rand_y = random.randint(starting_trench_coord[1][0], starting_trench_coord[1][1])

                trench_waypoint_graph = starting_trench.get_waypoint_graph()

                soldier = Soldier(Coordinate(rand_x, rand_y), 20, 20, trench_waypoint_graph, self.__countries[sides],
                                  self.__group)

                bolt_action_rifle = Gun(Coordinate(500, 500), 10, 10, "none",
                                        10, 10, 10,
                                        self.__group)

                soldier.set_weapon(bolt_action_rifle)

    def __initialize_artillery(self, trenches_coords):
        artillery_height = 20
        total_artillery = self.__height // artillery_height
        trench_distance = 400

        new_x = 0
        new_y = 0

        for side in range(0, 2):
            new_x = 0
            artillery_space = 0
            side_trench_coord = trenches_coords[side]
            support_trench_coord = side_trench_coord[0]

            if side == 0:   # Left side minus x coord
                new_x = support_trench_coord[0] - trench_distance
            elif side == 1:   # Right side add x coord
                new_x = support_trench_coord[0] + trench_distance

            for artillery_count in range(total_artillery):
                artillery = Artillery(Coordinate(new_x, new_y + artillery_space), 50, 20,
                                      10, 10, 100,
                                      side_trench_coord, self.__group)

                artillery_space += (self.__height // artillery_height)