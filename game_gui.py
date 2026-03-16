from abc import ABC, abstractmethod

import pygame

import npc
from coordinate import Coordinate
from game_mechanics import Actor


class UserInterface(Actor, ABC):
    def __init__(self, coord, width, height, group):
        super().__init__(coord, width, height, group)

        self._show = False

    def set_show(self, show):
        self._show = show

    def is_shown(self):
        return self._show

    def set_diameters(self, width, height):
        self._width = width
        self._height = height


class SelectBox(UserInterface):
    OUTLINE_COLOUR = (0, 0, 0)

    def __init__(self, coord, country, width, height, group):
        super().__init__(coord, width, height, group)
        self._rect = pygame.Rect(0, 0, 0, 0)
        self._country = country
        self._start_pos = None
        self._pressed = False

    def draw(self, screen, camera):
        screen_rect = camera.translate_rect(self._rect)

        if self._pressed:
            pygame.draw.rect(screen, self.OUTLINE_COLOUR, screen_rect, 3)

    def act(self, mouse_pos):
        self.execute(mouse_pos)

    def execute(self, mouse_pos):
        if not self._pressed:
            return

        self._update(mouse_pos)
        # self._select(soldiers)

    def _update(self, mouse_pos):
        start_x, start_y = self._start_pos.get_x(), self._start_pos.get_y()
        current_x, current_y = mouse_pos[0], mouse_pos[1]

        rect_x = min(start_x, current_x)
        rect_y = min(start_y, current_y)
        rect_w = abs(start_x - current_x)
        rect_h = abs(start_y - current_y)

        self._rect = pygame.Rect(rect_x, rect_y, rect_w, rect_h)

    def end_drag(self, npc_actors):
        if not self._pressed:
            return

        self._pressed = False
        self._select_actors(npc_actors)

        self._rect = pygame.Rect(0, 0, 0, 0)

    def _select_actors(self, npc_actors):
        for actor in npc_actors:
            if isinstance(actor, npc.Soldier):
                if (self.has_collided(actor) and
                        actor.get_country() == self._country):
                    actor.set_select(True)
                else:
                    actor.set_select(False)

    def pressed(self, mouse_pos):
        self._pressed = True
        self._start_pos = Coordinate(mouse_pos[0], mouse_pos[1])

    def is_pressed(self):
        return self._pressed


class Button(UserInterface):
    def __init__(self, coord, width, height, group, colour, pressed_colour, text, text_size, text_colour):
        super().__init__(coord, width, height, group)
        self._colour = colour
        self._pressed_colour = pressed_colour
        self._outline_colour = (0, 0, 0)
        self._rect = pygame.Rect(coord.get_coord(), (width, height))

        self._text_size = text_size
        self._text_colour = text_colour
        self._text = text
        self._text_font = pygame.font.SysFont("verdana", self._text_size).render(text, True, text_colour)
        self._text_rect = self._text_font.get_rect()

    def draw(self, screen, camera=None):
        pygame.draw.rect(screen, self._colour, self._rect)
        # Outline rect
        pygame.draw.rect(screen, self._outline_colour, self._rect, 4)
        # Text
        self._text_rect.center = self._rect.center
        screen.blit(self._text_font, self._text_rect)

    def act(self):
        self._check_pressed()
        self._update_rect()

    def _update_rect(self):
        self._rect = pygame.Rect(self._world_coord.get_coord(), (self._width, self._height))
        self._text_font = pygame.font.SysFont("verdana", self._text_size).render(self._text, True,
                                                                                 self._text_colour)

    def _check_pressed(self):
        if self._select:
            self._outline_colour = self._pressed_colour
        else:
            self._outline_colour = (0, 0, 0)

    def has_collided(self, other):
        if isinstance(other, tuple):
            return self._rect.collidepoint(other)

    def set_text_size(self, text_size):
        self._text_size = text_size

    def set_text_colour(self, text_colour):
        self._text_colour = text_colour


class Icon(UserInterface):
    def __init__(self, coord, width, height, group, text, image_path):
        super().__init__(coord, width, height, group)

        self._image = pygame.image.load(image_path)
        self._image_rect = self._image.get_rect()

        self._text = text
        self._text_size = 20
        self._font = pygame.font.SysFont("verdana", self._text_size)
        self._text_font = self._font.render(self._text, True, (0, 0, 0))
        self._text_rect = self._text_font.get_rect()

    def draw(self, screen, camera):
        screen_rect = camera.translate_rect(self._image_rect)

        screen_rect_x = screen_rect.centerx
        screen_rect_y = screen_rect.centery

        screen.blit(self._image, screen_rect)

        self._text_rect.x = screen_rect_x + self._image_rect.width
        self._text_rect.y = screen_rect_y - self._height

        screen.blit(self._text_font, self._text_rect)

    def act(self, mouse_pos):
        pass

    def resize(self, width, height):
        self._image = pygame.transform.scale(self._image, (width, height))
        self._image_rect = self._image.get_rect()

    def set_text_size(self, text_size):
        self._text_size = text_size
        self._font = pygame.font.SysFont("verdana", self._text_size)

    def has_collided(self, other):
        pass


class InteractiveTab(UserInterface):
    def __init__(self, coord, width, height, group):
        super().__init__(coord, width, height, group)

        self._num_sections = 0
        self._max_sections = self._width // self._width
        self._section_spaced = self._width // self._max_sections
        self._colour = (255, 255, 255)

        self._sections = []

    def draw(self, screen, camera):
        pygame.draw.rect(screen, self._colour, self._rect)

    def act(self, mouse_pos):
        pass

    def add_icon(self, icon):
        if self._num_sections > self._max_sections:
            print("Unable to add the icon.")
            return

        icon.resize(50, self._height)
        icon.set_text_size(10)

        self._num_sections += 1
        self._sections.append(icon)

    def get_sections(self):
        return self._sections


class TextBox(UserInterface):
    SIDEBAR = '|'

    def __init__(self, coord, width, height, group, colour, prompt_message, npc_list):
        super().__init__(coord, width, height, group)

        self._body_rect = pygame.Rect(coord.get_coord(), (width, height))
        self._text = []
        self._text_colour = (128, 255, 0)
        self._text_size = 20
        self._colour = colour
        self._active = False

        self._text_font = pygame.font.SysFont("verdana", self._text_size).render(self.get_text_str(True), True,
                                                                                 self._text_colour)
        self._prompt_text = f"{prompt_message} > "
        self._prompt_font = pygame.font.SysFont("verdana", self._text_size).render(self._prompt_text, True,
                                                                                   self._text_colour)
        self._prompt_rect = self._prompt_font.get_rect()
        self._text_rect = self._text_font.get_rect()
        self._cursor_index = 0

    def draw(self, screen, camera=None):
        if self._show:
            spaces_after_prompt = self._prompt_font.get_width()
            # Drawing the body
            pygame.draw.rect(screen, self._colour, self._body_rect)
            # Drawing the text
            self._prompt_rect = (self._body_rect.x, self._body_rect.y)
            self._text_rect = (
                self._body_rect.x + spaces_after_prompt,
                self._body_rect.y)  # The text needs to be placed after the prompt

            screen.blit(self._prompt_font, self._prompt_rect)
            screen.blit(self._text_font, self._text_rect)

    def act(self, mouse_pos):
        self._update_rect()

    def _update_rect(self):
        self._text_font = pygame.font.SysFont("verdana", self._text_size).render(self.get_text_str(True), True,
                                                                                 self._text_colour)
        self._prompt_font = pygame.font.SysFont("verdana", self._text_size).render(self._prompt_text, True,
                                                                                   self._text_colour)

    def insert_char(self, char):
        self._text.insert(self._cursor_index, char)
        self._cursor_index += 1

    def remove_char(self):
        if len(self._text) > 0:
            self._text.pop()

    def _clear_text(self):
        self._text.clear()

    def get_text_str(self, sidebar):
        if not self._active or not sidebar:
            return ''.join(self._text)

        rendered = (
                self._text[:self._cursor_index]
                + ['|']
                + self._text[self._cursor_index:]
        )
        return ''.join(rendered)

    def set_active(self, active):
        if active:
            self._clear_text()

        self._active = active

    def is_active(self):
        return self._active

    def has_collided(self, mouse_pos):
        return self._body_rect.collidepoint(mouse_pos)


class Console(TextBox):
    def __init__(self, coord, width, height, group, colour, prompt_symbol, field_waypoints, trench_list, npc_list):
        super().__init__(coord, width, height, group, colour, prompt_symbol, npc_list)

        print(trench_list)
        self._commands = {
            "debug_trenches = true": lambda: [t.set_debug(True) for t in trench_list],
            "debug_field = true": lambda: field_waypoints.set_debug(True),
            "debug_trenches = false": lambda: [t.set_debug(False) for t in trench_list],
            "debug_field = false": lambda: field_waypoints.set_debug(False),
            "remove_all_soldiers": lambda: group.remove_all(npc.Soldier),
            "debug_morale = true": lambda: [n.show_morale() for n in npc_list.get_actors()],
            "debug_morale = false": lambda: [n.hide_morale() for n in npc_list.get_actors()]
        }
        self._colour = colour

    def execute_command(self):
        text = self.get_text_str(False)

        if text is not None:
            print(text)
            if text in self._commands:
                self._commands[text]()

        self._clear_text()


class HUI(UserInterface):
    def __init__(self, text, colour, coord, width, height, group):
        super().__init__(coord, width, height, group)

        self._npc = None
        self._colour = colour
        self._outline_colour = (0, 0, 0)

        self._text = text
        self._font = pygame.font.SysFont("verdana", 5)  # load once
        self._text_font = self._font.render(self._text, True, (0, 0, 0))
        self._text_rect = self._text_font.get_rect()

    def act(self, mouse_pos):
        self._update_rect()

    def _update_rect(self):
        self._rect = pygame.Rect(self._world_coord.get_coord(), (self._width, self._height))

    def _update_text(self, text):
        self._text = text
        self._text_font = (pygame.font.SysFont("verdana", 5).
                           render(text, True, (0, 0, 0)))


class MoraleBar(HUI):
    def __init__(self, text, colour, coord, width, height, group):
        super().__init__(text, colour, coord, width, height, group)

        self._npc_morale = 0
        self._morale_bar_rect = pygame.Rect(coord.get_coord(), (self._npc_morale, self._height))

    def act(self, mouse_pos):
        super().act(mouse_pos)

        self._update_morale()
        self._lock_to_npc()

    def draw(self, screen, camera):
        if self._show:
            screen_rect = camera.translate_rect(self._morale_bar_rect)
            pygame.draw.rect(screen, self._colour, screen_rect)
            pygame.draw.rect(screen, self._outline_colour, screen_rect, 2)

    def _update_morale(self):
        self._npc_morale = self._npc.get_morale()

        self._morale_bar_rect = pygame.Rect(self._world_coord.get_coord(),
                                            (self._npc_morale, self._height))

    def _lock_to_npc(self):
        npc_center_x = self._npc.get_rect().centerx
        npc_center_y = self._npc.get_rect().centery

        new_x = npc_center_x - self._width // 2
        new_y = (npc_center_y - self._height // 2) - self._height * 2

        self._world_coord = Coordinate(new_x, new_y)

    def set_npc(self, n):
        self._npc = n