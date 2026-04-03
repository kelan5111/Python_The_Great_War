from game_gui import *
from game_mechanics import *
from npc import *
from trench import *
from weapon_resources import *


class Battlefield:
    def __init__(self, screen, screen_width, screen_height, player_country):

        self._screen = screen

        self._screen_width = screen_width
        self._screen_height = screen_height

        self._trenches = {}

        self._countries = [Country.BRITAIN, Country.GERMANY]
        self._player_country = player_country
        self._ai_country = Country.GERMANY
        self._player_fighting_direction = player_country.value["fighting_direction"]
        self._ai_fighting_direction = self._ai_country.value["fighting_direction"]
        self._fighting_directions = [FightingDirection.WEST, FightingDirection.EAST]

        self._world_camera = Camera(screen_width, screen_height)
        self._field_waypoints = Graph(screen_width + (screen_width // 2), screen_height, 30)
        self._field_waypoints.build()

        self._ground_colour = (48, 35, 9)

        self._npc_group = NPCGroup(screen)
        self._weapon_group = WeaponGroup(screen)
        self._particle_group = ParticleGroup(screen)
        self._environment_group = EnvironmentGroup(screen)
        self._ui_group = UIGroup(screen)

        self._initialize()

    def draw(self):
        self._screen.fill(self._ground_colour)

        self._particle_group.draw(self._world_camera)
        self._environment_group.draw(self._world_camera)
        self._npc_group.draw(self._world_camera)
        self._weapon_group.draw(self._world_camera)
        self._ui_group.draw(self._world_camera)

        # self._field_waypoints.draw(self._screen, self._world_camera)

    def act(self, raw_mouse_pos, dt):
        camera_mouse_pos = self._world_camera.translate_mouse_pos(raw_mouse_pos)

        self._manage_camera_input(dt)

        self._npc_group.act(camera_mouse_pos)
        self._weapon_group.act(camera_mouse_pos)
        self._particle_group.act(camera_mouse_pos)
        self._environment_group.act(camera_mouse_pos)
        self._ui_group.act(camera_mouse_pos)

    def _initialize(self):
        pygame.display.set_caption('The Great War')

        self._initialize_waypoints()
        self._initialize_trenches()
        self._initialize_soldiers(10)
        self._initialize_ui()
        self._initialize_artillery()

    def _initialize_ui(self):
        all_trenches = [t for sublist in self._trenches.values() for t in sublist]

        select_box = SelectBox(Coordinate(0, 0), self._player_country, 0, 0, self._ui_group)

        console = Console(Coordinate(0, self._screen_height - 40), self._screen_width, 200, self._ui_group,
                          (0, 0, 0), '[CONSOLE]', self._field_waypoints, all_trenches, self._npc_group)

        interactive_tab = InteractiveTab(Coordinate(0, 0), self._screen_width, 40, self._ui_group)

        morale_icon_image_path = "assets/images/morale_icon.png"

    def _initialize_waypoints(self):
        self._field_waypoints.build()
        self._field_waypoints.draw(self._screen, self._world_camera)

    def _initialize_soldiers(self, num_soldiers):
        for fighting_direction in self._fighting_directions:
            starting_trench = self._trenches["front_line"][fighting_direction.value["name"]]
            starting_trench_prox = starting_trench.get_proximity()

            self._initialize_commanders(fighting_direction, starting_trench, starting_trench_prox)

            for soldier_count in range(num_soldiers):
                rand_x = random.randint(starting_trench_prox[0][0], starting_trench_prox[0][1])
                rand_y = random.randint(starting_trench_prox[1][0], starting_trench_prox[1][1])

                trench_waypoint_graph = starting_trench.get_waypoint_graph()

                soldier = Soldier(Coordinate(rand_x, rand_y), 20, 20, trench_waypoint_graph,
                                  self._countries[fighting_direction.value["id"]],
                                  self._npc_group)

                bolt_action_rifle = Gun(Coordinate(500, 500), 10, 10, "none",
                                        10, 10, 10,
                                        self._weapon_group)
                soldier.set_weapon(bolt_action_rifle)

                self._initialize_npc_ui(soldier)

    def _initialize_commanders(self, fighting_direction, starting_trench, starting_trench_prox):
        for rank in CommanderRank:
            rand_x = random.randint(starting_trench_prox[0][0], starting_trench_prox[0][1])
            rand_y = random.randint(starting_trench_prox[1][0], starting_trench_prox[1][1])
            new_coord = Coordinate(rand_x, rand_y)

            trench_waypoint_graph = starting_trench.get_waypoint_graph()

            commander = Commander(new_coord, 10, 10, trench_waypoint_graph,
                                  self._countries[fighting_direction.value["id"]],
                                  self._npc_group, rank)

            pistol = Gun(Coordinate(500, 500), 10, 10, "none",
                         10, 10, 10,
                         self._weapon_group)

            commander.set_weapon(pistol)

            self._initialize_npc_ui(commander)

    def _initialize_artillery(self):
        spaced = 70
        total_artillery = self._screen_height // spaced
        trench_distance = 400

        curr_y = 0

        for fighting_direction in self._fighting_directions:
            new_x = 0
            new_y = 0
            country = None

            friendly_sl_trench = self._trenches["support_line"][fighting_direction.value["name"]]
            friendly_fl_trench = self._trenches["front_line"][fighting_direction.value["name"]]

            friendly_sl_prox = friendly_sl_trench.get_proximity()[0]
            friendly_fl_prox = friendly_fl_trench.get_proximity()[0]

            enemy_sl_prox = None
            enemy_fl_prox = None
            enemy_sl_trench = None
            enemy_fl_trench = None

            if fighting_direction == FightingDirection.WEST:  # left side minus x coord
                country = self._player_country

                enemy_sl_trench = self._trenches["support_line"]["east"]
                enemy_fl_trench = self._trenches["front_line"]["east"]

                new_x = friendly_sl_prox[0] - trench_distance

            elif fighting_direction == FightingDirection.EAST:  # right side add x coord
                country = self._ai_country

                enemy_sl_trench = self._trenches["support_line"]["west"]
                enemy_fl_trench = self._trenches["front_line"]["west"]

                new_x = friendly_sl_prox[0] + trench_distance

            enemy_sl_prox = enemy_sl_trench.get_proximity()[0]
            enemy_fl_prox = enemy_fl_trench.get_proximity()[0]

            for artillery_count in range(total_artillery):
                new_y += (curr_y + spaced)

                starting_pos = Coordinate(new_x, new_y)

                artillery = Artillery(starting_pos, 50, 20, 10, 10, 5,
                                      friendly_sl_prox, friendly_fl_prox, enemy_sl_prox, enemy_fl_prox,
                                      self._weapon_group, self._field_waypoints, country)

                gunner = Gunner(starting_pos, 0, 20, self._field_waypoints, country, self._npc_group)

                gunner.set_curr_state(NPCState.ENGAGED)
                gunner.set_weapon(artillery)

                self._initialize_npc_ui(gunner)

                artillery.add_soldier(gunner)

    def _initialize_npc_ui(self, n):
        morale_bar = Bar(n, (62, 192, 105), Coordinate(0, 0), 100, 10, self._ui_group)
        n.set_morale_bar(morale_bar)

        if isinstance(n, Soldier):
            base_image_path = 'assets/images/board_ui.png'
            panel_width = self._screen_width // 1.2
            panel_height = self._screen_height * 1.2

            stats_panel = SoldierStatsPanel(n, self._screen_width, self._screen_height, base_image_path,
                                            Coordinate(0, 0), panel_width, panel_height, self._ui_group)

    def _initialize_trenches(self):
        space_between_fl_x = 100
        space_between_sl_x = -200

        front_line_west = FrontLineTrench(Coordinate(space_between_fl_x, 0), 50, self._screen_height, 10,
                                          self._player_country,
                                          self._ground_colour, self._npc_group.get_actors(), self._environment_group)
        support_line_west = SupportTrench(Coordinate(space_between_sl_x, 0), 50, self._screen_height, 50,
                                          self._player_country,
                                          self._ground_colour, self._npc_group.get_actors(), self._environment_group)
        communication_trench_west = CommunicationTrench(support_line_west, front_line_west, 0, Country.BRITAIN,
                                                        self._ground_colour, self._npc_group.get_actors(),
                                                        self._environment_group)

        front_line_east = FrontLineTrench(Coordinate(self._screen_width - space_between_fl_x, 0), 50,
                                          self._screen_height, 10, Country.GERMANY,
                                          self._ground_colour, self._npc_group.get_actors(), self._environment_group)
        support_line_east = SupportTrench(Coordinate(self._screen_width - space_between_sl_x, 0), 50,
                                          self._screen_height, 50, Country.GERMANY,
                                          self._ground_colour, self._npc_group.get_actors(), self._environment_group)
        communication_trench_east = CommunicationTrench(support_line_east, front_line_east, 0, Country.GERMANY,
                                                        self._ground_colour, self._npc_group.get_actors(),
                                                        self._environment_group)

        front_line_east.add_comm_trenches(communication_trench_east)
        support_line_east.add_comm_trenches(communication_trench_east)
        front_line_west.add_comm_trenches(communication_trench_west)
        support_line_west.add_comm_trenches(communication_trench_west)

        self._trenches["front_line"] = {"west": front_line_west, "east": front_line_east}
        self._trenches["support_line"] = {"west": support_line_west, "east": support_line_east}
        self._trenches["communication"] = {"west": communication_trench_west, "east": communication_trench_east}

    def manage_input(self, event, mouse_pos):
        camera_mouse_pos = self._world_camera.translate_mouse_pos(mouse_pos)

        self._manage_mouse_input(event, camera_mouse_pos)
        self._manage_key_input(event)

    def _manage_mouse_input(self, event, camera_mouse_pos):

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
                                npc.has_collided(camera_mouse_pos)):
                            npc.set_select(True)

                morale_bar = [actor for actor in self._ui_group.get_actors() if isinstance(actor, Bar)]

                for ui in self._ui_group.get_actors():
                    if isinstance(ui, Button):
                        ui.set_select(True)

            # Any soldier is selected they will move to mouse pos
            if event.button == 3:
                for npc in self._npc_group.get_actors():
                    if isinstance(npc, Soldier):
                        if npc.has_selected():
                            selectable_trenches = [
                                self._trenches["front_line"][self._player_fighting_direction.value["name"]],
                                self._trenches["support_line"][self._player_fighting_direction.value["name"]]
                                ]

                            for trench in selectable_trenches:
                                if trench.has_collided(camera_mouse_pos):
                                    npc.switch_trenches(trench)

                                    trench.set_select(False)

        if event.type == pygame.MOUSEBUTTONDOWN:
            console = self._ui_group.find(Console)

            if event.button == 1:
                select_box = self._ui_group.find(SelectBox)
                interactive_tab = self._ui_group.find(InteractiveTab)

                select_box.pressed(camera_mouse_pos)

                # If a text box is selected
                if console.has_collided(camera_mouse_pos):
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

    def _manage_camera_input(self, dt):
        keys = pygame.key.get_pressed()

        # Manage the movement of the camera
        if keys[pygame.K_d]:
            self._world_camera.update(Direction.RIGHT, dt)
        elif keys[pygame.K_a]:
            self._world_camera.update(Direction.LEFT, dt)
