import pygame
from pygame import key

from waypoint import Graph, Node
from coordinate import Coordinate
from npc import Soldier, Country, Weapon

WIDTH = 1280
HEIGHT = 720
waypoints = []

soldiers = []
others = []


def draw(screen, waypoint_graph):
    draw_NPCs(screen)
    # Waypoint
    waypoint_graph.draw(screen)


def build_waypoints(waypoint_graph):
    GAP = 40
    temp = []

    for x in range(0, WIDTH, GAP):
        column = []  # Create a new empty column for every X
        for y in range(0, HEIGHT, GAP):
            column.append(Node(Coordinate(x + GAP, y + GAP)))  # Add nodes to the column
        temp.append(column)

    # Building the graph
    waypoint_graph.build_graph(temp)


def manage_death(soldier):
    return not soldier.is_alive()


def draw_NPCs(screen):
    # Draw soldiers
    for soldier in soldiers:
        soldier.draw(screen)
        soldier.update(soldiers)

        if not soldier.is_alive():
            soldiers.remove(soldier)

    for other in others:
        other.draw(screen)
        other.update()


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    running = True

    waypoint_graph = Graph(WIDTH, HEIGHT)

    # Building
    build_waypoints(waypoint_graph)

    # Starting pos for npc
    british_start_pos = waypoint_graph.breadth_first_search(None, 1)
    germany_start_pos = waypoint_graph.breadth_first_search(None, 25)
    british_soldier = Soldier(british_start_pos, Country.BRITAIN)
    german_soldier = Soldier(germany_start_pos, Country.GERMANY)

    b_weapon = Weapon("none", british_soldier)
    g_weapon = Weapon("none", german_soldier)
    others.append(b_weapon)
    others.append(g_weapon)

    british_soldier.arm_with_weapon(b_weapon)
    german_soldier.arm_with_weapon(g_weapon)
    soldiers.append(british_soldier)
    soldiers.append(german_soldier)

    while running:
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.MOUSEBUTTONUP:
                if pygame.mouse.get_pressed() and event.button == 1:
                    for soldier in soldiers:
                        # Selecting a soldier
                        if soldier.is_selected(mouse_pos):
                            soldier.select()
                        else:
                            soldier.unselect()

                if pygame.mouse.get_pressed() and event.button == 3:
                    for soldier in soldiers:
                        if soldier.has_selected():
                            soldier.set_path(waypoint_graph, mouse_pos)
                            soldier.unselect()

        screen.fill((48, 35, 9))

        # Draw objects
        draw(screen, waypoint_graph)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
