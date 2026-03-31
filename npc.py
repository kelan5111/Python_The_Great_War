import enum
from typing import List

import pygame
from enum import Enum

from coordinate import Coordinate, Direction
from abc import ABC, abstractmethod

from sprite_resources import SpriteSheet
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
        self._colour = (255, 0, 0)
        self._border_colour = (0, 0, 0)
        self._regiment_colour = (0, 0, 0)
        self._rect = pygame.Rect(self._world_coord.get_coord(), (self._width, self._height))
        self._ID = NPC.ID + 1

        self._animation_timer = Timer()

        self._idle_timer = Timer()
        self._curr_idle_time = 0

        self._hub_timer = Timer()

        self._speed = NPC.SPEED
        self._actors = group.get_actors()

        self._morale = 100
        self._morale_bar = morale_bar
        self._show_morale_bar = False

        self._curr_trench = None
        self._path = []
        self._curr_waypoint_graph = waypoint_graph
        self._next_waypoint_graph = None
        self._target_waypoint = None

        self._curr_direction = Direction.UP
        self._curr_state = NPCState.IDLE
        self._moving = False
        self._debug = False

        if coord is not None:
            self._curr_waypoint = self._curr_waypoint_graph.find_nearest_waypoint(coord.get_coord())
            self._world_coord = self._curr_waypoint.get_coord()

    def draw(self, screen, camera):
        screen_rect = camera.translate_rect(self._rect)
        border_thickness = 2

        if self._select:
            self._border_colour = (255, 255, 255)
            self._draw_debug(screen, camera)
        else:
            self._border_colour = self._regiment_colour

    def _draw_debug(self, screen, camera):
        radius = 10
        colour = (255, 0, 0)

        if self._target_waypoint is not None:
            waypoint_coord = self._target_waypoint.get_coord().get_coord()
            screen_coord = camera.translate_coord(waypoint_coord)

            pygame.draw.circle(screen, colour, screen_coord, radius)

            trench_rect = camera.translate_rect(self._curr_trench.get_rect())
            pygame.draw.rect(screen, (0, 0, 0), trench_rect)

            print(self)

    def act(self, mouse_pos):
        self._execute_idle_movement()
        self._execute_controlled_movement()
        self._update_sprite()

        self._move()

    def __str__(self):
        return f"NPC: {self._country, self._world_coord, self._target_waypoint, self._path}"

    def _execute_idle_movement(self):
        neighbours = []

        if self._curr_state == NPCState.IDLE:
            if not self.has_path() and self._target_waypoint is None:
                neighbours = self._curr_waypoint.get_neighbours()

            if len(neighbours) > 0:
                if self._idle_cooldown():
                    next_coord = random.choice(neighbours).get_coord()
                    self.set_path(next_coord)

    def _idle_cooldown(self):
        if not self._idle_timer.is_started():
            self._idle_timer.start()
            self._curr_idle_time = random.randint(1, 4)

        if self._idle_timer.is_finished(self._curr_idle_time):
            self._idle_timer.reset()
            return True

        return False

    def _execute_controlled_movement(self):
        if self.has_path() and not self._moving:
            self._target_waypoint = self._path.pop()

            if self._next_waypoint_graph is not None:
                self._switch_waypoint_graph()

    def _move(self):
        if self._target_waypoint is not None:
            target_coord = self._target_waypoint.get_coord()

            dist_x = abs(self._world_coord.get_x() - target_coord.get_x())
            dist_y = abs(self._world_coord.get_y() - target_coord.get_y())

            self._moving = True

            if dist_x <= NPC.SPEED and dist_y <= NPC.SPEED:
                self._curr_waypoint = self._target_waypoint
                self._target_waypoint = None  # Clear target so controlled_movement grabs the next one
                return

            if self._curr_trench is None:
                next_coord = self._calc_movement(target_coord)
            else:
                next_coord = self._calc_trench_movement(target_coord)

            self._world_coord = next_coord

        elif self._target_waypoint is None:
            self._moving = False

    def set_path(self, target_coord=None, waypoint_id=None):
        if target_coord is not None:  # If we want to move to a certain coord (find the closest waypoint)
            self._target_waypoint = self._curr_waypoint_graph.find_nearest_waypoint(target_coord)
            path = self._curr_waypoint_graph.build_path([], waypoint_id, self._curr_waypoint,
                                                        self._target_waypoint)
        else:
            path = self._curr_waypoint_graph.build_path([], waypoint_id, self._curr_waypoint, None)

        if path is not None:
            self._path = path
            self._target_waypoint = None

    def _calc_movement(self, target_coord):
        step = 1
        new_x = self._world_coord.get_x()
        new_y = self._world_coord.get_y()
        target_x = target_coord.get_x()
        target_y = target_coord.get_y()

        if new_x < target_x:
            new_x += (step * NPC.SPEED)
            self._curr_direction = Direction.RIGHT

        elif new_x > target_x:
            new_x -= (step * NPC.SPEED)
            self._curr_direction = Direction.LEFT

        if new_y < target_y:
            new_y += (step * NPC.SPEED)
            self._curr_direction = Direction.DOWN

        elif new_y > target_y:
            new_y -= (step * NPC.SPEED)
            self._curr_direction = Direction.UP

        elif not self._moving:
            self._curr_direction = Direction.UP

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
            self._curr_direction = Direction.RIGHT

        elif new_x > target_x:
            new_x -= (step * NPC.SPEED)
            self._curr_direction = Direction.LEFT

        if new_y < target_y:
            new_y += (step * NPC.SPEED)
            self._curr_direction = Direction.DOWN

        elif new_y > target_y:
            new_y -= (step * NPC.SPEED)
            self._curr_direction = Direction.UP

        elif not self._moving:
            self._curr_direction = Direction.UP

        return Coordinate(new_x, new_y)

    def _switch_waypoint_graph(self):
        self._curr_waypoint_graph = self._next_waypoint_graph
        self._next_waypoint_graph = None

    @abstractmethod
    def _attack(self):
        pass

    def _update_sprite(self):
        self._rect = pygame.Rect(self._world_coord.get_coord(), (self._width, self._height))

    def set_next_waypoint_graph(self, waypoint_graph):
        self._next_waypoint_graph = waypoint_graph

    def get_curr_waypoint_graph(self):
        return self._curr_waypoint_graph

    def get_country(self):
        return self._country

    def is_idle(self):
        return self._curr_state == NPCState.IDLE

    def show_moral_bar(self):
        self._morale_bar.set_show(True)

    def hide_moral_bar(self):
        self._morale_bar.set_show(False)

    def set_morale(self, morale):
        self._morale = morale

    def get_morale(self):
        return self._morale

    def has_path(self):
        return len(self._path) > 0

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

    def set_curr_state(self, curr_state):
        self._curr_state = curr_state


class Soldier(NPC):
    def __init__(self, coord, width, height, curr_waypoint_graph, country, group, morale_bar, weapon=None):
        super().__init__(coord, width, height, curr_waypoint_graph, country, group, morale_bar)

        self._country = country
        self._regiment_colour = self._colour
        self._weapon = weapon
        self._enemy_lock = None
        self._shot_chance = 100
        self._shell_shocked = False

        self._sprite = SpriteSheet(self._country.value["sprite_sheet_path"])
        self._animations = self._set_animations()
        self._animation_cooldown = 0.5
        self._frame = 0
        self._trench_path = {}

    def __str__(self):
        return f"Soldier: {self._ID}, Country: {self._country}, Waypoint: {self._curr_waypoint}"

    def draw(self, screen, camera):
        super().draw(screen, camera)

        screen_rect = camera.translate_rect(self._rect)

        if self._frame >= 3:  # Reset the frames once its reached max
            self._frame = 0

        img = self._animations["walking"][self._curr_direction][self._frame]
        img_rect = img.get_rect()
        img_rect.center = screen_rect.center
        screen.blit(img, img_rect)

        if not self._animation_timer.is_started():
            self._animation_timer.start()

        if self._animation_timer.is_finished(self._animation_cooldown):
            self._frame += 1
            self._animation_timer.reset()

    def _set_animations(self):
        animations = {}
        image_list = self._sprite.get_sprite_list(4, 3, 64, 64, 2, (0, 0, 0))

        animations["walking"] = {
            Direction.UP: image_list[3:6],
            Direction.DOWN: image_list[0:3],
            Direction.LEFT: image_list[9:12],
            Direction.RIGHT: image_list[6:9]
        }

        return animations

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
        for actor in self._actors:
            if isinstance(actor, Soldier):
                if actor.get_country() != self._country:
                    enemy = self._is_enemy_near(actor)

                    if enemy is not None:  # Enemy is near, stop moving and engage
                        self._curr_state = NPCState.ENGAGED
                        self._enemy_lock = enemy
                        self._attack()
                    else:  # No enemy is in sight act normal
                        self._curr_state = NPCState.IDLE
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
            if self._curr_state == NPCState.ENGAGED:
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
            self._trench_path["state"] = "moving_to_target_trench"

            self._curr_waypoint_graph = comm_trench.get_waypoint_graph()
            self._curr_waypoint = self._curr_waypoint_graph.find_nearest_waypoint(self._world_coord.get_coord())

            entrance_points = comm_trench.get_entrance_points()
            entry_name = self._trench_path["entrance_name"]

            exit_name = "right_entrance" if entry_name == "left_entrance" else "left_entrance"
            exit_tuple = entrance_points[exit_name]
            exit_coord = Coordinate(exit_tuple[0], exit_tuple[1])

            self.set_path(exit_coord)

        elif state == "moving_to_target_trench" and not self._moving:
            self._curr_waypoint_graph = target_trench.get_waypoint_graph()
            self._curr_waypoint = self._curr_waypoint_graph.find_nearest_waypoint(self._world_coord.get_coord())

            self._trench_path.clear()

    def switch_trenches(self, target_trench):
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
            self._debug = True
        elif not select and not self._shell_shocked:
            self.hide_moral_bar()
            self._debug = False

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

            if not self._hub_timer.is_started():
                self._hub_timer.start()

            if self._hub_timer.is_finished(5):
                self._shell_shocked = False
                self._morale_bar.set_show(False)
                self._hub_timer.reset()

    def retreat(self):
        pass

    def is_shell_shocked(self):
        return self._shell_shocked

    def is_moving(self):
        return self._moving


class Commander(Soldier):
    def __init__(self, coord, width, height, curr_waypoint_graph, country, group, morale_bar, command_type):
        super().__init__(coord, width, height, curr_waypoint_graph, country, group, morale_bar)

        self._commander_rank: CommanderRank = command_type
        self._unit: Unit = Unit()


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

        self.curr_state = NPCState.ENGAGED

    def act(self, mouse_pos):
        super().act(mouse_pos)

        if self.has_weapon():
            self._weapon.shoot_random_projectile(self._actors)
            self._lock_to_weapon()

    def _monitor_select(self):
        pass

    def _lock_to_weapon(self):
        self._world_coord = self._weapon.get_coord()


class Unit:
    def __init__(self):
        self._unit = List[Soldier] = []

    def move_all(self, target_coord):
        for soldier in self._unit:
            soldier.set_path(target_coord)

    def add_soldier(self, soldier):
        self._unit.append(soldier)

    def remove_soldier(self, soldier):
        self._unit.remove(soldier)

    def get_soldier(self):
        return self._unit


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
    # Need to implement the sprite sheet as a reference
    BRITAIN = {
        "sprite_sheet_path": "assets/images/sprite_sheets/british_soldier_walk-Sheet.png",
        "fighting_direction": FightingDirection.WEST
    }
    GERMANY = {
        "sprite_sheet_path": "assets/images/sprite_sheets/german_soldier_walk-Sheet.png",
        "fighting_direction": FightingDirection.EAST
    }


class NPCState(enum.Enum):
    ENGAGED = 0
    IDLE = 1


class NPCMood(enum.Enum):
    NEUTRAL = 1
    SCARED = 2
    ANGRY = 3


class CommanderRank(enum.Enum):
    SERGENT = 0
    SECOND_LIEUTENANT = 1
    LIEUTENANT = 2
    CAPTAIN = 3
    MAJOR = 4
    COLONEL = 5



