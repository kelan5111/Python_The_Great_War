import pygame
from enum import Enum

from coordinate import Coordinate, Direction
from abc import ABC, abstractmethod
from game_mechanics import Actor, Timer
import random


class NPC(Actor):
    ID = 0
    SPEED = 0.5
    SIZE = 15

    def __init__(self, coord, width, height, waypoint_graph, country, group, morale_bar):
        super().__init__(coord, width, height, group)
        self._width = NPC.SIZE
        self._height = NPC.SIZE
        self._country = country
        self._colour = country.value["colour"]
        self._border_colour = (0, 0, 0)
        self._regiment_colour = (0, 0, 0)
        self._rect = pygame.Rect(self._world_coord.get_coord(), (self._width, self._height))
        self._ID = NPC.ID + 1

        self._timer = Timer()

        self._speed = NPC.SPEED
        self._actors = group.get_actors()

        self._morale = 100
        self._morale_bar = morale_bar
        self._show_morale_bar = False

        self._engaged = False
        self._moving = False
        self._idle = True
        self._curr_trench = None

        self._path = []
        self._curr_waypoint_graph = waypoint_graph
        self._next_waypoint_graph = None
        self._target_waypoint = None

        self._debug_mode = False

        if coord is not None:
            self._curr_waypoint = self._curr_waypoint_graph.find_nearest_waypoint(coord.get_coord())
            self._world_coord = self._curr_waypoint.get_coord()

    def draw(self, screen, camera):
        screen_rect = camera.translate_rect(self._rect)
        border_thickness = 2

        if self._select:
            self._border_colour = (255, 255, 255)
        else:
            self._border_colour = self._regiment_colour

        pygame.draw.rect(screen, self._colour, screen_rect)
        pygame.draw.rect(screen, self._border_colour, screen_rect, border_thickness)

        self._draw_path(screen, camera)

    def _draw_path(self, screen, camera):
        radius = 10
        colour = (255, 0, 0)

        if self._debug_mode:
            for waypoint in self._path:
                waypoint_coord = waypoint.get_coord().get_coord()
                screen_coord = camera.translate_coord(waypoint_coord)

                pygame.draw.circle(screen, colour, screen_coord, radius)

    def act(self, mouse_pos):
        self._execute_idle_movement()
        self._execute_controlled_movement()

    def _execute_idle_movement(self):
        if self._idle and not self._moving:
            neighbours = self._curr_waypoint.get_neighbours()
            next_coord = random.choice(neighbours).get_coord()
            self.set_path(next_coord)

    def _execute_controlled_movement(self):
        if not self._engaged:
            if self._target_waypoint is None:
                if len(self._path) > 0:
                    self._target_waypoint = self._path.pop()
                else:
                    if self._next_waypoint_graph is not None:
                        self._switch_waypoint_graph()

                    self._moving = False
                    return

            target_coord = self._target_waypoint.get_coord()

            dist_x = abs(self._world_coord.get_x() - target_coord.get_x())
            dist_y = abs(self._world_coord.get_y() - target_coord.get_y())

            if dist_x <= NPC.SPEED and dist_y <= NPC.SPEED:
                self._update_rect(target_coord)
                self._curr_waypoint = self._target_waypoint
                self._target_waypoint = None
                return

            if self._curr_trench is None:
                next_coord = self._calc_movement(target_coord)
            else:
                next_coord = self._calc_trench_movement(target_coord)

            self._update_rect(next_coord)

    def set_path(self, target_coord=None, waypoint_id=None):
        if target_coord is not None:  # If we want to move to a certain coord (find the closest waypoint)
            self._target_waypoint = self._curr_waypoint_graph.find_nearest_waypoint(target_coord)
            path = self._curr_waypoint_graph.build_path([], waypoint_id, self._curr_waypoint,
                                                        self._target_waypoint)
        else:
            path = self._curr_waypoint_graph.build_path([], waypoint_id, self._curr_waypoint, None)

        if path is not None:
            self._moving = True
            self._path = path
            self._target_waypoint = None
        else:
            self._moving = False

    def _calc_movement(self, target_coord):
        step = 1
        new_x = self._world_coord.get_x()
        new_y = self._world_coord.get_y()
        target_x = target_coord.get_x()
        target_y = target_coord.get_y()

        if new_x < target_x:
            new_x += (step * NPC.SPEED)
        elif new_x > target_x:
            new_x -= (step * NPC.SPEED)

        if new_y < target_y:
            new_y += (step * NPC.SPEED)
        elif new_y > target_y:
            new_y -= (step * NPC.SPEED)

        return Coordinate(new_x, new_y)

    def _is_enemy_near(self, enemy):
        if enemy.get_country() != self._country:
            enemy_coord = enemy.get_coord()
            danger = self._world_coord.execute_radius_check(enemy_coord)
            if danger:
                return enemy

        return None

    def _calc_trench_movement(self, target_coord):
        step = 1
        new_x = self._world_coord.get_x()
        new_y = self._world_coord.get_y()
        target_x = target_coord.get_x()
        target_y = target_coord.get_y()

        trench_rect = self._curr_trench.get_rect()

        if new_x < target_x:
            new_x += (step * NPC.SPEED)
        elif new_x > target_x:
            new_x -= (step * NPC.SPEED)

        if new_y < target_y:
            new_y += (step * NPC.SPEED)
        elif new_y > target_y:
            new_y -= (step * NPC.SPEED)

        return Coordinate(new_x, new_y)

    def _switch_waypoint_graph(self):
        # Swap the current with the new graph after current path is finished
        self._curr_waypoint_graph = self._next_waypoint_graph
        self._next_waypoint_graph = None

        self.set_path(self._world_coord)

    @abstractmethod
    def _attack(self):
        pass

    def _update_rect(self, coord):
        self._world_coord = coord
        self._rect = pygame.Rect(self._world_coord.get_coord(), (self._width, self._height))

    def set_idle(self, idle):
        self._idle = idle

    def set_next_waypoint_graph(self, waypoint_graph):
        self._next_waypoint_graph = waypoint_graph

    def get_curr_waypoint_graph(self):
        return self._curr_waypoint_graph

    def get_country(self):
        return self._country

    def is_idle(self):
        return self._idle

    def set_debug_mode(self, deug_mode):
        self._debug_mode = deug_mode

    def show_moral_bar(self):
        self._morale_bar.set_show(True)

    def hide_moral_bar(self):
        self._morale_bar.set_show(False)

    def set_morale(self, morale):
        self._morale = morale

    def get_morale(self):
        return self._morale

    def set_select(self, select):
        if select:
            self.show_moral_bar()
        elif not select:
            self.hide_moral_bar()

        self._select = select

    def set_curr_trench(self, curr_trench):
        self._curr_trench = curr_trench

    def get_curr_trench(self):
        return self._curr_trench


class Soldier(NPC):
    def __init__(self, coord, width, height, curr_waypoint_graph, country, group, morale_bar, weapon=None):
        super().__init__(coord, width, height, curr_waypoint_graph, country, group, morale_bar)

        self._country = country
        self._regiment_colour = self._colour
        self._weapon = weapon
        self._enemy_lock = None
        self._shot_chance = 100
        self._shell_shocked = False

        self._trench_path = {}

    def __str__(self):
        return f"Soldier: {self._ID}, Country: {self._country}, Waypoint: {self._curr_waypoint}"

    def act(self, mouse_pos):
        super().act(mouse_pos)

        self._detect_enemies()
        self._monitor_shell_shocked()
        self._monitor_trenches()

    def kill(self):
        self._alive = False
        if self.has_weapon():
            self._weapon.kill()
        self._remove_weapon()

        self._morale_bar.kill()

    def _detect_enemies(self):
        if not self._idle:
            for actor in self._actors:
                if isinstance(actor, Soldier):
                    if actor.get_country() != self._country:
                        enemy = self._is_enemy_near(actor)

                        if enemy is not None:  # Enemy is near, stop moving and engage
                            self._engaged = True
                            self._enemy_lock = enemy
                            self._attack()
                        else:  # No enemy is in sight act normal
                            self._engaged = False
                            self._enemy_lock = None

    def _attack(self):
        if self.has_weapon():
            shot_success = self._calc_shot_chance()
            if shot_success:
                self._weapon.shoot(self._enemy_lock, self._actors)

    def _calc_shot_chance(self):
        if self.has_weapon():
            random_chance = random.randint(0, 100)
            moving = 30

            # Negative factors contributing to the shot chance
            if self._moving:
                self._shot_chance -= moving

            # Measuring the chances against random num
            if random_chance <= self._shot_chance:
                return True

        return False

    def _monitor_trenches(self):
        target_trench = self._trench_path.get("target")

        if target_trench is None:
            return

        state = self._trench_path.get("state")
        comm_trench = self._trench_path.get("comm")

        if state == "moving_to_comm" and not self._moving:
            self._trench_path["state"] = "in_comm_trench"

            self.set_curr_trench(comm_trench)
            self.set_next_waypoint_graph(comm_trench.get_waypoint_graph())
            self._path.clear()

            entrance_points = comm_trench.get_entrance_points()
            entry_name = self._trench_path["entrance_name"]

            exit_name = "right_entrance" if entry_name == "left_entrance" else "left_entrance"
            exit_tuple = entrance_points[exit_name]
            exit_coord = Coordinate(exit_tuple[0], exit_tuple[1])

            self.set_path(exit_coord)

        elif state == "in_comm_trench" and not self._moving:
            self.set_curr_trench(target_trench)
            self.set_next_waypoint_graph(target_trench.get_waypoint_graph())

            self._trench_path.clear()
            self.set_idle(True)

    def switch_trenches(self, target_trench):
        self._idle = False

        self._trench_path["target"] = target_trench
        self._trench_path["comm"] = target_trench.get_comm_trenches()[0]
        self._trench_path["state"] = "moving_to_comm"

        comm_trench = self._trench_path["comm"]
        entrance_points = comm_trench.get_entrance_points()

        curr_closest_name = None
        curr_closest_coord = None
        min_distance = float("inf")

        for entry_name, entry_tup in entrance_points.items():
            distance = self._world_coord.calculate_distance(entry_tup)

            if distance < min_distance:
                min_distance = distance
                curr_closest_name = entry_name
                curr_closest_coord = entry_tup

        if curr_closest_coord is not None:
            self._trench_path["entrance_name"] = curr_closest_name
            self.set_path(curr_closest_coord)

    def set_select(self, select):
        if select:
            self.show_moral_bar()
        elif not select and not self._shell_shocked:
            self.hide_moral_bar()

        self._select = select

    def set_weapon(self, weapon):
        weapon.set_owner(self)
        self._weapon = weapon

    def _remove_weapon(self):
        self._weapon.remove_owner()

    def has_weapon(self):
        return self._weapon is not None

    def get_weapon(self):
        return self._weapon

    def get_shot_chance(self):
        return self._shot_chance

    def set_shell_shocked(self, shell_shocked):
        self._shell_shocked = shell_shocked

    def _monitor_shell_shocked(self):
        if self._shell_shocked:
            self._morale_bar.set_show(True)

            if not self._timer.is_started():
                self._timer.start()

            if self._timer.is_finished(5):
                self._shell_shocked = False
                self._morale_bar.set_show(False)
                self._timer.reset()

    def is_shell_shocked(self):
        return self._shell_shocked

    def is_moving(self):
        return self._moving


class SpecialForces(Soldier):
    def __init__(self, coord, width, height, curr_waypoint_graph, country, group, morale_bar):
        super().__init__(coord, width, height, curr_waypoint_graph, country, group, morale_bar)

        self._skill_lvl = 0

    def get_skill_lvl(self):
        return self._skill_lvl


class Gunner(SpecialForces):
    def __init__(self, coord, width, height, curr_waypoint_graph, country, group, morale_bar):
        super().__init__(coord, width, height, curr_waypoint_graph, country, group, morale_bar)

        self._regiment_colour = (0, 0, 153)
        self._world_coord = coord

    def act(self, mouse_pos):
        super().act(mouse_pos)

        if self._weapon is not None:
            self._weapon.shoot_random_projectile(self._actors)

    def _monitor_select(self):
        pass


class FightingDirection(Enum):
    WEST = {
        "id": 0,
        "name": "west"
    }
    EAST = {
        "id": 1,
        "name": "east"
    }


class Country(Enum):
    BRITAIN = {
        "colour": pygame.color.Color(107, 94, 65),
        "fighting_direction": FightingDirection.WEST
    }
    GERMANY = {
        "colour": pygame.color.Color(75, 83, 72),
        "fighting_direction": FightingDirection.EAST
    }


class WeaponType(Enum):
    pass
