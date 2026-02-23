from abc import ABC, abstractmethod

import pygame

import npc
from coordinate import Coordinate
from game_mechanics import Actor


class SelectBox(Actor, ABC):
    OUTLINE_COLOUR = (0, 0, 0)

    def __init__(self, country):
        super().__init__(coord=Coordinate(0, 0), width=0, height=0)
        self._rect = pygame.Rect(0, 0, 0, 0)
        self.__country = country
        self.__start_pos = None
        self.__pressed = False

    def draw(self, screen, camera):
        screen_rect = camera.translate_rect(self._rect)

        if self.__pressed:
            pygame.draw.rect(screen, self.OUTLINE_COLOUR, screen_rect, 3)

    def act(self, mouse_pos):
        self.execute(mouse_pos)

    def execute(self, mouse_pos):
        if not self.__pressed:
            return

        self.__update(mouse_pos)
        # self.__select(soldiers)

    def __update(self, mouse_pos):
        start_x, start_y = self.__start_pos.get_x(), self.__start_pos.get_y()
        current_x, current_y = mouse_pos[0], mouse_pos[1]

        rect_x = min(start_x, current_x)
        rect_y = min(start_y, current_y)
        rect_w = abs(start_x - current_x)
        rect_h = abs(start_y - current_y)

        self._rect = pygame.Rect(rect_x, rect_y, rect_w, rect_h)

    def end_drag(self, actors):
        if not self.__pressed:
            return

        self.__pressed = False
        self.__select(actors)

        self._rect = pygame.Rect(0, 0, 0, 0)

    def __select(self, actors):
        for actor in actors:
            if isinstance(actor, npc.Soldier):
                if (self.has_collided(actor) and
                        actor.get_country() == self.__country):
                    actor.set_select(True)
                else:
                    actor.set_select(False)

    def pressed(self, mouse_pos):
        self.__pressed = True
        self.__start_pos = Coordinate(mouse_pos[0], mouse_pos[1])

    def is_pressed(self):
        return self.__pressed


class UserInterface(ABC):
    def __init__(self, coord=None, width=None, height=None, image=None):
        self._world_coord = coord
        self.__screen_coord = Coordinate(0, 0)

        self._width = width
        self._height = height
        self._image = image

        self._select = False
        self._hover = False
        self._show = False

    @abstractmethod
    def draw(self, screen, camera=None):
        pass

    @abstractmethod
    def update(self):
        pass

    @abstractmethod
    def has_collided(self, other):
        pass

    # Setters and getters
    def set_select(self, select):
        self._select = select

    def has_selected(self):
        return self._select

    def set_hover(self, hover):
        self._hover = hover

    def set_show(self, show):
        self._show = show

    def is_shown(self):
        return self._show

    def set_diameters(self, width, height):
        self._width = width
        self._height = height

    def set_coord(self, x, y):
        self._world_coord = Coordinate(x, y)

    def get_coord(self):
        return self._world_coord

    def get_width(self):
        return self._width

    def get_height(self):
        return self._height


class Button(UserInterface):
    def __init__(self, colour, pressed_colour, text, text_size, text_colour, coord=Coordinate(0, 0), width=0, height=0):
        super().__init__(coord, width, height)
        self.__colour = colour
        self.__pressed_colour = pressed_colour
        self.__outline_colour = (0, 0, 0)
        self.__rect = pygame.Rect(coord.get_coord(), (width, height))

        self.__text_size = text_size
        self.__text_colour = text_colour
        self.__text = text
        self.__text_font = pygame.font.SysFont("verdana", self.__text_size).render(text, True, text_colour)
        self.__text_rect = self.__text_font.get_rect()

    def draw(self, screen, camera=None):
        pygame.draw.rect(screen, self.__colour, self.__rect)
        # Outline rect
        pygame.draw.rect(screen, self.__outline_colour, self.__rect, 4)
        # Text
        self.__text_rect.center = self.__rect.center
        screen.blit(self.__text_font, self.__text_rect)

    def update(self):
        self.__check_pressed()
        self._update_rect()

    def _update_rect(self):
        self.__rect = pygame.Rect(self._world_coord.get_coord(), (self._width, self._height))
        self.__text_font = pygame.font.SysFont("verdana", self.__text_size).render(self.__text, True,
                                                                                   self.__text_colour)

    def __check_pressed(self):
        if self._select:
            self.__outline_colour = self.__pressed_colour
        else:
            self.__outline_colour = (0, 0, 0)

    def has_collided(self, other):
        if isinstance(other, tuple):
            return self.__rect.collidepoint(other)

    def set_text_size(self, text_size):
        self.__text_size = text_size

    def set_text_colour(self, text_colour):
        self.__text_colour = text_colour


class Icon(UserInterface):
    def __init__(self, coord, width, height, image_path):
        super().__init__(coord, width, height)

        self.__image = image_path

    def draw(self, screen, camera=None):
        pass

    def update(self):
        pass

    def has_collided(self, other):
        pass


class InteractiveTab:
    def __init__(self, screen_width):
        self.__width = screen_width
        self.__height = 40
        self.__coord = Coordinate(0, 0)
        self.__body_rect = pygame.Rect(self.__coord.get_coord(), (self.__width, self.__height))

        self.__ui_width = 40
        self.__ui_height = self.__height

        self.__num_sections = 0
        self.__max_sections = self.__width // self.__ui_width
        self.__section_spaced = self.__width // self.__max_sections
        self.__colour = (255, 255, 255)

        self.__sections = []

    def draw(self, screen, camera):
        pygame.draw.rect(screen, self.__colour, self.__body_rect)
        # Drawing the sections
        for ui in self.__sections:
            ui.draw(screen, camera)

    def update(self):
        for ui in self.__sections:
            ui.update()

    def add_icon(self, ui):
        if self.__num_sections > self.__max_sections:
            print("Unable to add the icon.")
            return

        self.__resize_ui(ui)
        self.__num_sections += 1
        self.__sections.append(ui)

    def __resize_ui(self, ui):
        new_x = self.__num_sections * self.__section_spaced
        new_y = new_x

        ui.set_coord(new_x, new_y)
        ui.set_diameters(self.__ui_width, self.__ui_height)
        ui.set_text_size(2)

    def get_sections(self):
        return self.__sections


class TextBox(UserInterface):
    SIDEBAR = '|'

    def __init__(self, coord, width, height, colour, prompt_message):
        super().__init__(coord, width, height)

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

    def update(self):
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
    def __init__(self, coord, width, height, colour, prompt_symbol, field_waypoints, trench_list):
        super().__init__(coord, width, height, colour, prompt_symbol)

        self.__commands = {
            "debug_trenches = true": lambda: [t.set_debug(True) for t in trench_list],
            "debug_field = true": lambda: field_waypoints.set_debug(True),
            "debug_trenches = false": lambda: [t.set_debug(False) for t in trench_list]
        }
        self.__colour = (0, 0, 0)

    def execute_command(self):
        text = self.get_text_str(False)

        if text is not None:
            print(text)
            if text in self.__commands:
                self.__commands[text]()

        self._clear_text()