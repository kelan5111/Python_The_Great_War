import pygame
import random

from waypoint import Graph
from coordinate import Coordinate, Direction
from npc import Soldier, Country, FightingDirection, Gunner, NPC
from weapon_resources import Gun, Artillery
from game_mechanics import (NPCGroup, WeaponGroup, ParticleGroup, UIGroup,
                            Timer, Camera, ParticleGroup, EnvironmentGroup)
from game_gui import SelectBox, Button, InteractiveTab, Console, MoraleBar, Icon
from trench import FrontLineTrench, SupportTrench, Trench, CommunicationTrench


class Game:
    def __init__(self, width, height, player_country):
        self._countries = [Country.BRITAIN, Country.GERMANY]
        self._player_country = player_country
        self._ai_country = Country.GERMANY
        self._player_fighting_direction = player_country.value[1]
        self._ai_fighting_direction = self._ai_country.value[1]
        self._fighting_directions = [FightingDirection.WEST, FightingDirection.EAST]

        self._width = width
        self._height = height
        self._screen = pygame.display.set_mode((width, height), pygame.FULLSCREEN, vsync=1)
        self._dt = 0.0

        self._world_camera = Camera(self._width, self._height)

        self._width = width
        self._height = height
        self._ground_colour = (48, 35, 9)
        self._running = True

        self._npc_group = NPCGroup(self._screen)
        self._weapon_group = WeaponGroup(self._screen)
        self._particle_group = ParticleGroup(self._screen)
        self._environment_group = EnvironmentGroup(self._screen)
        self._ui_group = UIGroup(self._screen)

        self._trenches = {}

        self._field_waypoints = Graph(self._width + (self._width // 2), self._height, 30)
        self._field_waypoints.build()
        self._timer = Timer()

    def run(self):
        clock = pygame.time.Clock()

        self._initialize()

        while self._running:
            world_mouse_pos = pygame.mouse.get_pos()
            screen_mouse_pos = self._world_camera.translate_mouse_pos(world_mouse_pos)
            self._dt = clock.tick(60) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._running = False

                self._manage_input(event, screen_mouse_pos)

            self._act(screen_mouse_pos)
            self._manage_camera_input()
            self._draw()

            pygame.display.flip()
            clock.tick(60)

        pygame.quit()

    def _draw(self):
        self._screen.fill(self._ground_colour)

        self._particle_group.draw(self._world_camera)
        self._environment_group.draw(self._world_camera)
        self._ui_group.draw(self._world_camera)
        self._npc_group.draw(self._world_camera)
        self._weapon_group.draw(self._world_camera)

        self._field_waypoints.draw(self._screen, self._world_camera)

    def _act(self, mouse_pos):
        self._npc_group.act(mouse_pos)
        self._weapon_group.act(mouse_pos)
        self._particle_group.act(mouse_pos)
        self._environment_group.act(mouse_pos)
        self._ui_group.act(mouse_pos)

    def _initialize_ui(self):
        all_trenches = [t for sublist in self._trenches.values() for t in sublist]

        select_box = SelectBox(Coordinate(0, 0), self._player_country, 0, 0, self._ui_group)

        console = Console(Coordinate(0, self._height - 40), self._width, 200, self._ui_group,
                          (0, 0, 0), '[CONSOLE]', self._field_waypoints, all_trenches, self._npc_group)

        interactive_tab = InteractiveTab(Coordinate(0, 0), self._width, 40, self._ui_group)

        morale_icon_image_path = "assets/images/morale_icon.png"
        morale_icon = Icon(Coordinate(0, 0), 0, 0, self._ui_group, "morale", morale_icon_image_path)

        interactive_tab.add_icon(morale_icon)

    def _initialize(self):
        pygame.display.set_caption('The Great War')

        self._initialize_waypoints()
        self._initialize_trenches()
        self._initialize_ui()
        self._initialize_soldiers(10)
        self._initialize_artillery()

    def _initialize_waypoints(self):
        self._field_waypoints.build()
        self._field_waypoints.draw(self._screen, self._world_camera)

    def _manage_input(self, event, mouse_pos):
        self._manage_mouse_input(event, mouse_pos)
        self._manage_key_input(event)

    def _manage_mouse_input(self, event, mouse_pos):

        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                select_box = self._ui_group.find(SelectBox)
                interactive_tab = self._ui_group.find(InteractiveTab)

                # If we are dragging a select box
                if select_box.is_pressed():
                    select_box.end_drag(self._npc_group.get_actors())

                for npc in self._npc_group.get_actors():
                    if isinstance(npc, NPC):
                        if (npc.get_country() == self._player_country and
                                npc.has_collided(mouse_pos)):
                            npc.set_select(True)

                morale_bar = [actor for actor in self._ui_group.get_actors() if isinstance(actor, MoraleBar)]

                for section in interactive_tab.get_sections():
                    if isinstance(section, Button):
                        section.set_select(False)

            # Any soldier is selected they will move to mouse pos
            if event.button == 3:
                for npc in self._npc_group.get_actors():
                    if isinstance(npc, Soldier):
                        if npc.has_selected():
                            if not npc.is_idle():
                                npc.set_path(mouse_pos)
                                npc.set_select(False)
                            else:
                                all_trenches = [
                                    trench for trench_list in self._trenches.values() for trench in trench_list
                                ]

                                for trench in all_trenches:
                                    if trench.has_collided(mouse_pos):
                                        trench_waypoints = trench.get_waypoint_graph()

                                        npc.set_next_waypoint_graph(trench_waypoints)
                                        trench.set_select(False)

        if event.type == pygame.MOUSEBUTTONDOWN:
            console = self._ui_group.find(Console)

            if event.button == 1:
                select_box = self._ui_group.find(SelectBox)
                interactive_tab = self._ui_group.find(InteractiveTab)

                select_box.pressed(mouse_pos)

                for section in interactive_tab.get_sections():
                    if section.has_collided(mouse_pos):
                        if isinstance(section, Button):
                            section.set_select(True)

                # If a text box is selected
                if console.has_collided(mouse_pos):
                    console.set_active(True)
                else:
                    console.set_active(False)

            # Select Trench
            if event.button == 3:
                for actor in self._environment_group.get_actors():
                    if isinstance(actor, Trench) and actor.get_country() == self._player_country:
                        if actor.has_hover():
                            actor.set_select(True)

    def _manage_key_input(self, event):
        if event.type == pygame.KEYDOWN:
            console = self._ui_group.find(Console)

            if event.key == pygame.K_BACKSLASH:
                if console.is_shown():
                    console.set_show(False)
                else:
                    console.set_active(True)
                    console.set_show(True)

            elif console.is_active():
                # Managing the consoles text input
                if event.key == pygame.K_RETURN:
                    console.execute_command()

                elif event.key == pygame.K_BACKSPACE:
                    console.remove_char()
                else:
                    console.insert_char(event.unicode)

    def _manage_camera_input(self):
        keys = pygame.key.get_pressed()

        # Manage the movement of the camera
        if keys[pygame.K_d]:
            self._world_camera.update(Direction.RIGHT, self._dt)
        elif keys[pygame.K_a]:
            self._world_camera.update(Direction.LEFT, self._dt)

    def _initialize_soldiers(self, num_soldiers):
        support_trenches = self._trenches.get("support_line")
        support_trenches_prox = [slt.get_proximity() for slt in support_trenches]

        for sides in range(0, 2):
            for soldier_count in range(num_soldiers):
                starting_trench = support_trenches[sides]
                starting_trench_coord = support_trenches_prox[sides]

                rand_x = random.randint(starting_trench_coord[0][0], starting_trench_coord[0][1])
                rand_y = random.randint(starting_trench_coord[1][0], starting_trench_coord[1][1])

                trench_waypoint_graph = starting_trench.get_waypoint_graph()

                morale_bar = MoraleBar("", (62, 192, 105), Coordinate(0, 0), 10, 10, self._ui_group)
                soldier = Soldier(Coordinate(rand_x, rand_y), 20, 20, trench_waypoint_graph, self._countries[sides],
                                  self._npc_group, morale_bar)

                bolt_action_rifle = Gun(Coordinate(500, 500), 10, 10, "none",
                                        10, 10, 10,
                                        self._weapon_group)

                morale_bar.set_npc(soldier)
                soldier.set_weapon(bolt_action_rifle)

    def _initialize_artillery(self):
        spaced = 70
        total_artillery = self._height // spaced
        trench_distance = 400

        support_lines_prox = [slt.get_proximity() for slt in self._trenches.get("support_line")]
        front_lines_prox = [flt.get_proximity() for flt in self._trenches.get("front_line")]

        curr_y = 0

        for fighting_direction in self._fighting_directions:
            new_x = 0
            new_y = 0
            country = None

            friendly_support_trench_coord = support_lines_prox[fighting_direction.value][0]
            friendly_front_line_coord = front_lines_prox[fighting_direction.value][0]
            enemy_support_trench_coord = None
            enemy_front_line_coord = None

            if fighting_direction == FightingDirection.WEST:  # left side minus x coord
                country = self._player_country

                enemy_support_trench_coord = support_lines_prox[FightingDirection.EAST.value][0]
                enemy_front_line_coord = front_lines_prox[FightingDirection.WEST.value][0]

                new_x = friendly_support_trench_coord[0] - trench_distance

            elif fighting_direction == FightingDirection.EAST:  # right side add x coord
                country = self._ai_country

                enemy_support_trench_coord = support_lines_prox[FightingDirection.WEST.value][0]
                enemy_front_line_coord = front_lines_prox[FightingDirection.WEST.value][0]

                new_x = friendly_support_trench_coord[0] + trench_distance

            for artillery_count in range(total_artillery):
                new_y += (curr_y + spaced)

                starting_pos = Coordinate(new_x, new_y)

                artillery = Artillery(starting_pos, 50, 20, 10, 10, 5,
                                      friendly_support_trench_coord, enemy_support_trench_coord,
                                      friendly_front_line_coord, enemy_front_line_coord,
                                      self._weapon_group, self._field_waypoints, country)

                morale_bar = MoraleBar("", (62, 192, 105), Coordinate(0, 0), 10, 10, self._ui_group)
                gunner = Gunner(starting_pos, 0, 20, self._field_waypoints, country, self._npc_group, morale_bar)
                morale_bar.set_npc(gunner)
                gunner.set_idle(False)
                gunner.set_weapon(artillery)

                artillery.add_soldier(gunner)

    def _initialize_trenches(self):
        front_line_west = FrontLineTrench(Coordinate(400, 0), 50, self._height, 10, self._player_country,
                                          self._ground_colour, self._npc_group.get_actors(), self._environment_group)
        support_line_west = SupportTrench(Coordinate(100, 0), 50, self._height, 50, self._player_country,
                                          self._ground_colour, self._npc_group.get_actors(), self._environment_group)
        communication_trench_west = CommunicationTrench(support_line_west, front_line_west, 0, Country.BRITAIN,
                                                   self._ground_colour, self._npc_group.get_actors(), self._environment_group)

        front_line_east = FrontLineTrench(Coordinate(self._width - 400, 0), 50, self._height, 10, Country.GERMANY,
                                          self._ground_colour, self._npc_group.get_actors(), self._environment_group)
        support_line_east = SupportTrench(Coordinate(self._width - 100, 0), 50, self._height, 50, Country.GERMANY,
                                          self._ground_colour, self._npc_group.get_actors(), self._environment_group)
        communication_trench_east = CommunicationTrench(support_line_east, front_line_east, 0, Country.GERMANY,
                                                        self._ground_colour, self._npc_group.get_actors(),
                                                        self._environment_group)

        self._trenches["front_line"] = [front_line_west, front_line_east]
        self._trenches["support_line"] = [support_line_west, support_line_east]
        self._trenches["communication"] = [communication_trench_west, communication_trench_east]