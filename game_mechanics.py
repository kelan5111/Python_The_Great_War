import pygame
from coordinate import Coordinate


class SelectBox:
    OUTLINE_COLOUR = (0, 0, 0)

    def __init__(self, country):
        self.__shape = pygame.Rect(0, 0, 0, 0)
        self.__country = country
        self.__start_pos = None
        self.__pressed = False

    def draw(self, screen):
        if self.__pressed:
            pygame.draw.rect(screen, self.OUTLINE_COLOUR, self.__shape, 3)

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

        self.__shape = pygame.Rect(rect_x, rect_y, rect_w, rect_h)

    def end_drag(self, soldier_list):
        if not self.__pressed:
            return

        self.__pressed = False
        self.__select(soldier_list)

        self.__shape = pygame.Rect(0, 0, 0, 0)

    def __select(self, soldier_list):
        for soldier in soldier_list:
            if (soldier.get_shape().colliderect(self.__shape) and
                    soldier.get_country() == self.__country):
                soldier.select()
            else:
                soldier.unselect()

    def update(self):
        pass

    def pressed(self, mouse_pos):
        self.__pressed = True
        self.__start_pos = Coordinate(mouse_pos[0], mouse_pos[1])

    def is_pressed(self):
        return self.__pressed
