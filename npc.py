import pygame
from enum import Enum
from coordinate import Coordinate
from abc import ABC, abstractmethod


class NPC:
    ID = 0
    WIDTH = 20
    HEIGHT = 20

    def __init__(self, waypoint, country):
        self._curr_waypoint = waypoint
        self._coord = waypoint.get_coord()
        self._country = country
        self._colour = country.value
        self._shape = pygame.Rect(self._coord.get_coord(), (NPC.WIDTH, NPC.HEIGHT))
        self._ID = NPC.ID + 1

        self._alive = True

        self._path = []
        self._target_waypoint = None

    def draw(self, screen):
        pygame.draw.rect(screen, self._colour, self._shape)

    def set_path(self, waypoint_graph, target_coord=None, waypoint_id=None):
        if target_coord is not None:  # If we want to move to a certain coord (find the closest waypoint)
            self._target_waypoint = waypoint_graph.find_nearest_waypoint(target_coord)
            path = waypoint_graph.build_path([], waypoint_id, self._curr_waypoint, self._target_waypoint)
        else:
            path = waypoint_graph.build_path([], waypoint_id, self._curr_waypoint, None)

        if path is not None:
            self._path = path
            self._target_waypoint = None

    def update(self, soldier_list=None):
        if self._target_waypoint is None:
            if self._path:
                self._target_waypoint = self._path.pop()
            else:
                return

        target_coord = self._target_waypoint.get_coord()

        if self._coord.get_coord() == target_coord.get_coord():
            self._curr_waypoint = self._target_waypoint
            self._target_waypoint = None
            return

        next_coord = self._calc_next_coord(target_coord)
        self._update(next_coord)

    def _calc_next_coord(self, target_coord):
        step = 1
        new_x = self._coord.get_x()
        new_y = self._coord.get_y()
        target_x = target_coord.get_x()
        target_y = target_coord.get_y()

        if new_x < target_x:
            new_x += step
        elif new_x > target_x:
            new_x -= step

        if new_y < target_y:
            new_y += step
        elif new_y > target_y:
            new_y -= step

        return Coordinate(new_x, new_y)

    def _is_enemy_near(self, enemy_list):
        for enemy in enemy_list:
            if enemy.get_country() != self._country:
                enemy_coord = enemy.get_coord()
                danger = self._coord.execute_radius_check(enemy_coord)
                if danger:
                    return enemy

        return None

    @abstractmethod
    def _attack(self):
        pass

    def _update(self, coord):
        self._coord = coord
        self._shape = pygame.Rect(self._coord.get_coord(), (NPC.WIDTH, NPC.HEIGHT))

    def is_alive(self):
        return self._alive

    def kill(self):
        self._alive = False

    def get_coord(self):
        return self._coord

    def get_country(self):
        return self._country

    # Setters and getters


class Soldier(NPC, ABC):
    def __init__(self, waypoint, country, weapon=None):
        super().__init__(waypoint, country)

        self._curr_waypoint = waypoint
        self._country = country
        self._weapon = weapon

        self._selected = False
        self._enemy_lock = None

    def __str__(self):
        return f"Soldier: {self._ID}, Country: {self._country}, Waypoint: {self._curr_waypoint}"

    def _detect_enemy(self, soldier_list):
        if soldier_list is not None:
            enemy = self._is_enemy_near(soldier_list)

            if enemy is not None:
                print("Enemy near")
                self._enemy_lock = enemy
                self._execute_attack()

    def draw(self, screen):
        pygame.draw.rect(screen, self._colour, self._shape)

        if self._selected:
            border_thickness = 2
            border_color = (255, 255, 255)
            pygame.draw.rect(screen, border_color, self._shape, border_thickness)

    def _draw_weapon(self):
        if self.has_weapon():
            self._weapon.show()

    def _execute_attack(self):
        if self.has_weapon():
            print("Attacking")
            self._weapon.shoot(self._enemy_lock)

    def update(self, soldier_list=None):
        super().update()

        self._detect_enemy(soldier_list)

    def arm_with_weapon(self, weapon):
        self._weapon = weapon
        self._weapon.set_owner(self)

    def disarm(self):
        self._weapon = None

    def kill(self):
        self._alive = False
        self._weapon = None

    def has_selected(self):
        return self._selected

    def is_selected(self, mouse_pos):
        return self._shape.collidepoint(mouse_pos)

    def select(self):
        self._selected = True

    def unselect(self):
        self._selected = False

    def has_weapon(self):
        return self._weapon is not None


class Weapon:
    AMMO_CAPACITY = 20
    WIDTH = 10
    HEIGHT = 20

    def __init__(self, gun_type, owner=None):
        self._shape = pygame.Rect((0, 0), (10, 10))
        self._colour = pygame.Color(0, 0, 0)

        self._gun_type = gun_type
        self._ammo = Weapon.AMMO_CAPACITY
        self._owner = owner
        self._coord = Coordinate(-100, -100)

    def __str__(self):
        return f"Gun{self._gun_type}: {self._owner}, capacity: {self._ammo}"

    def draw(self, screen):
        if self._owner is not None:
            pygame.draw.rect(screen, self._colour, self._shape)

    def _lock_to_owner(self):
        if self._owner is not None:
            owner_coord = self._owner.get_coord()
            self._coord = owner_coord

    def update(self):
        self._shape = pygame.Rect(self._coord.get_coord(), (Weapon.WIDTH, Weapon.HEIGHT))
        self._lock_to_owner()

    def shoot(self, target):
        target.kill()
        target.disarm()
        # need a weapon chance of killing

    def set_owner(self, owner):
        self._owner = owner


class Country(Enum):
    BRITAIN = pygame.color.Color(255, 0, 0)
    GERMANY = pygame.color.Color(127, 127, 127)


class WeaponType(Enum):
    pass
