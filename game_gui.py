import enum
from abc import ABC, abstractmethod
from typing import List

import pygame

from npc import Soldier
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


class InteractiveUI(UserInterface):
    def __init__(self, coord, width, height, group):
        super().__init__(coord, width, height, group)

        self._select = False
        self._show = False
        self._hover = False
        self._pressed = False

    def set_select(self, select):
        self._select = select

    def is_select(self):
        return self._select

    def set_hover(self, hover):
        self._hover = hover

    def is_hover(self):
        return self._hover

    def set_pressed(self, pressed):
        self._pressed = pressed

    def is_pressed(self):
        return self._pressed


class SelectBox(InteractiveUI):
    OUTLINE_COLOUR = (0, 0, 0)

    def __init__(self, npc_list, coord, country, width, height, group):
        super().__init__(coord, width, height, group)
        self._rect = pygame.Rect(0, 0, 0, 0)
        self._country = country
        self._start_pos = None
        self._npc_list = npc_list

    def draw(self, screen, camera):
        if self._pressed:
            screen_rect = camera.translate_rect(self._rect)

            pygame.draw.rect(screen, self.OUTLINE_COLOUR, screen_rect, 3)

    def act(self, mouse_pos):
        self._monitor_pressed(mouse_pos)

    def _update(self, mouse_pos):
        start_x, start_y = self._start_pos.get_x(), self._start_pos.get_y()
        current_x, current_y = mouse_pos[0], mouse_pos[1]

        rect_x = min(start_x, current_x)
        rect_y = min(start_y, current_y)
        rect_w = abs(start_x - current_x)
        rect_h = abs(start_y - current_y)

        self._rect = pygame.Rect(rect_x, rect_y, rect_w, rect_h)

    def end_drag(self):
        if not self._pressed:
            return

        self._pressed = False
        self._select_npc()

        self._start_pos = None
        self._rect = pygame.Rect(0, 0, 0, 0)

    def _select_npc(self):
        for npc in self._npc_list:
            if isinstance(npc, Soldier):
                if (self.has_collided(npc) and
                        npc.get_country() == self._country):
                    npc.set_select(True)
                else:
                    npc.set_select(False)

    def _monitor_pressed(self, mouse_pos):
        if self._pressed:

            if self._start_pos is None:
                self._start_pos = Coordinate(mouse_pos[0], mouse_pos[1])

            self._update(mouse_pos)


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


class TextBox(InteractiveUI):
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


class Console(TextBox):
    def __init__(self, coord, width, height, group, colour, prompt_symbol, field_waypoints, trench_list, npc_list):
        super().__init__(coord, width, height, group, colour, prompt_symbol, npc_list)

        self._commands = {
            "debug_trenches = true": lambda: [t.set_debug(True) for t in trench_list],
            "debug_field = true": lambda: field_waypoints.set_debug(True),
            "debug_trenches = false": lambda: [t.set_debug(False) for t in trench_list],
            "debug_field = false": lambda: field_waypoints.set_debug(False),
            "remove_all_soldiers": lambda: group.remove_all(Soldier),
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


class ObjectBoundUI(UserInterface):
    def __init__(self, attached_obj, coord, width, height, group):
        super().__init__(coord, width, height, group)

        self._attached_obj = attached_obj
        self._outline_colour = (0, 0, 0)

    def act(self, mouse_pos):
        self._update_rect()
        self._follow_obj()

    def _follow_obj(self):
        npc_center_x = self._attached_obj.get_rect().centerx
        npc_center_y = self._attached_obj.get_rect().centery

        new_x = npc_center_x - self._width // 2
        new_y = (npc_center_y - self._height // 2) - self._height * 2

        self._world_coord = Coordinate(new_x, new_y)

    def set_attached_obj(self, obj):
        self._attached_obj = obj

    def _update_rect(self):
        self._rect = pygame.Rect(self._world_coord.get_coord(), (self._width, self._height))


class Bar(ObjectBoundUI):
    def __init__(self, attached_object, bar_colour, coord, width, height, group):
        super().__init__(attached_object, coord, width, height, group)

        self._bar_colour = bar_colour
        self._bar_value = width

    def draw(self, screen, camera):
        if self._show:
            screen_rect = camera.translate_rect(self._rect)
            pygame.draw.rect(screen, self._bar_colour, screen_rect)
            pygame.draw.rect(screen, self._outline_colour, screen_rect, 2)

    def act(self, mouse_pos):
        super().act(mouse_pos)
        self._update_bar()

    def _update_bar(self):
        self._width = self._bar_value
    
    def set_bar_value(self, bar_value):
        self._bar_value = bar_value


class ScreenBoundUI(UserInterface):
    def __init__(self, screen_width, screen_height, coord, width, height, group):
        super().__init__(coord, width, height, group)

        self._screen_width = screen_width
        self._screen_height = screen_height

        self._anchor_pos = None

    def act(self, mouse_pos):
        self._monitor_anchoring_pos()

    def _monitor_anchoring_pos(self):
        if self._anchor_pos == AnchoringPosition.CENTER:
            self._anchor_center()
        elif self._anchor_pos == AnchoringPosition.CENTER_TOP:
            pass
        elif self._anchor_pos == AnchoringPosition.CENTER_BOTTOM:
            pass
        elif self._anchor_pos == AnchoringPosition.CENTER_LEFT:
            pass
        elif self._anchor_pos == AnchoringPosition.CENTER_RIGHT:
            pass
        elif self._anchor_pos == AnchoringPosition.TOP_RIGHT:
            pass
        elif self._anchor_pos == AnchoringPosition.BOTTOM_RIGHT:
            pass
        elif self._anchor_pos == AnchoringPosition.TOP_LEFT:
            pass
        elif self._anchor_pos == AnchoringPosition.BOTTOM_LEFT:
            pass
        else:
            raise "Invalid anchor position"

    def _anchor_center(self):
        self._rect.center = (self._screen_width // 2, self._screen_height // 2)
        self._world_coord = Coordinate(self._rect.centerx, self._rect.centery)

    def _anchor_top_left(self):
        pass

    def _anchor_bottom_right(self):
        pass

    def set_anchor_pos(self, anchor_pos):
        self._anchor_pos = anchor_pos


class Panel(ScreenBoundUI):
    def __init__(self, screen_width, screen_height, padding, base_image_path, coord, width, height, group):
        super().__init__(screen_width, screen_height, coord, width, height, group)

        self._base_image = pygame.image.load(base_image_path).convert_alpha()
        self._rect = self._base_image.get_bounding_rect()
        self._resize_base()

        self._children: List[UserInterface] = []

        self._padding = padding

        self.set_anchor_pos(AnchoringPosition.CENTER)

    def draw(self, screen, camera):
        if self._show:
            super().draw(screen, camera)

            screen.blit(self._base_image, self._rect)
    
    def act(self, mouse_pos):
        super().act(mouse_pos)

        self._monitor_children()

    def _resize_base(self):
        self._base_image = pygame.transform.scale(self._base_image, (self._width, self._height))
        visible_rect = self._base_image.get_bounding_rect()

        self._base_image = self._base_image.subsurface(visible_rect)
        self._rect = self._base_image.get_rect()

    def _monitor_children(self):
        if self._show:
            for child in self._children:
                child.set_show(True)

        self._update_layout()

    def _update_layout(self):
        padding_offset = 10
        padding_spacing = 50
        
        content_rect = self.get_content_rect()

        for child in self._children:
            child_rect = child.get_rect()
            new_x = content_rect.x + padding_offset
            new_y = content_rect.y + padding_offset + padding_spacing

            child_rect.topleft = (new_x, new_y)

    def add_child(self, child):
        self._children.append(child)

    def get_content_rect(self):
        return pygame.Rect(
            self._rect.x + self._padding,
            self._rect.y + self._padding,
            self._rect.width - 2 * self._padding,
            self._rect.height - 2 * self._padding
        )


class SoldierStatsPanel(Panel):
    def __init__(self, soldier, screen_width, screen_height, padding, base_image_path, coord, width, height, group):
        super().__init__(screen_width, screen_height, padding, base_image_path, coord, width, height, group)

        self._soldier = soldier

        self._exit_button = Button(coord, 50, 50, (255, 0, 0), (255, 255, 255), group)
        self._exit_button.set_attached_obj(self)

    def act(self, mouse_pos):
        super().act(mouse_pos)

        self._monitor_show()
        self._monitor_buttons()

    def draw(self, screen, camera):
        if self._show:
            # Draw the black background box
            pygame.draw.rect(screen, (255, 0, 0), self._rect, 3)
            # Draw the actual wooden board image on top
            screen.blit(self._base_image, self._rect)

    def _monitor_buttons(self):
        if self._exit_button.is_pressed():
            self.kill()

        self._update_buttons_pos()

    def _update_buttons_pos(self):
        new_x = self._rect.topleft[0] + 20
        new_y = self._rect.topleft[1] + 20
        self._exit_button.update_pos((new_x, new_y))

    def _monitor_show(self):
        if self._soldier.has_selected():
            self._show = True

    def kill(self):
        self._exit_button.kill()
        self._alive = False


class ToolTip(ObjectBoundUI):  # I DONT WANT THIS ATTACHED I WANT IT IN CENTRE OF SCREEN
    BASE_IMAGE_PATH = "assets/images/board_ui.png"

    def __init__(self, attached_obj, coord, width, height, group):
        super().__init__(attached_obj, coord, width, height, group)

        self._contents = []

        self._image = pygame.image.load(ToolTip.BASE_IMAGE_PATH)
        self._rect = self._image.get_rect()

    def draw(self, screen, camera):
        if self._show:
            screen_rect = camera.translate_rect(self._rect)
            screen.blit(self._image, screen_rect)

    def _resize_image(self):
        pygame.transform.scale(self._image, (self._width, self._height))


class TextContent:
    def __init__(self, text, text_colour, text_size):
        self._text = text
        self._text_colour = text_colour
        self._text_size = text_size

        self._font_obj = pygame.font.SysFont("verdana", text_size)
        self._font = pygame.font.SysFont("verdana", text_size)
        self._text_rect = self._font.get_rect()

        self.update()

    def draw(self, screen, camera):
        screen.blit(self._font, self._text_rect)

    def update(self):
        self._font = self._font_obj.render(self._text, True, self._text_colour)
        self._text_rect = self._font.get_rect()


class IconContent:
    def __init__(self, image_path):
        self._image = pygame.image.load(image_path)
        self._image_rect = self._image.get_rect()

    def draw(self, screen, coord):
        new_x = coord[0]
        new_y = coord[1]

        screen.blit(self._image, (new_x, new_y))
        self._image_rect.topleft = (new_x, new_y)

    def update(self):
        self._image_rect = self._image.get_rect()


class Button(InteractiveUI):
    def __init__(self, coord, width, height, colour, pressed_colour, group):
        super().__init__(coord, width, height, group)
        self._colour = colour
        self._pressed_colour = pressed_colour
        self._outline_colour = (0, 0, 0)
        self._rect = pygame.Rect(coord.get_coord(), (width, height))
        self._attached_obj = None

    def draw(self, screen, camera):
        if self._show:
            pygame.draw.rect(screen, self._colour, self._rect)
            # Outline rect
            pygame.draw.rect(screen, self._outline_colour, self._rect, 4)

    def act(self, mouse_pos):
        self._check_pressed()
        self._update_rect()

        self._monitor_attached_obj()

    def _update_rect(self):
        self._rect = pygame.Rect(self._world_coord.get_coord(), (self._width, self._height))

    def _check_pressed(self):
        if self._pressed:
            self._outline_colour = self._pressed_colour
        else:
            self._outline_colour = (0, 0, 0)

    def update_pos(self, coord):
        new_x, new_y = coord

        self._rect.center = (new_x, new_y)
        self._world_coord = Coordinate(new_x, new_y)

    def set_attached_obj(self, obj):
        self._attached_obj = obj

    def _monitor_attached_obj(self):
        if self._attached_obj is None:
            return

        if self._attached_obj.is_shown():
            self._show = True
        else:
            self._show = False


class AnchoringPosition(enum.Enum):
    CENTER = 0
    CENTER_LEFT = 1
    CENTER_RIGHT = 2
    CENTER_TOP = 3
    CENTER_BOTTOM = 4
    TOP_RIGHT = 5
    TOP_LEFT = 6
    BOTTOM_RIGHT = 7
    BOTTOM_LEFT = 8
