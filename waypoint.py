import pygame
from queue import Queue


class Node:
    RADIUS = 5
    next_id = 0

    def __init__(self, coord):
        self.__neighbours = []

        self.__ID = Node.next_id + 1
        self.__coord = coord
        self.__show = False
        self.__debug_colour = (128, 255, 0)

        self.__visited = False
        self.__distance = 0
        self.__parent = None

        Node.next_id += 1

    def __repr__(self):
        return f'Node ID: {self.__ID}: {self.__coord}'

    def draw(self, screen):
        DIAMETER = Node.RADIUS * 2
        invisible_surf = pygame.surface.Surface((DIAMETER, DIAMETER), pygame.SRCALPHA)

        if self.__show:
            # self._debug_colour = pygame.Color((128, 255, 0))

            pygame.draw.circle(screen, self.__debug_colour, (self.__coord.get_coord()), Node.RADIUS)
        else:
            pygame.draw.circle(invisible_surf, (0, 0, 0), (Node.RADIUS, Node.RADIUS), Node.RADIUS)
            screen.blit(invisible_surf, (self.__coord.get_x() - Node.RADIUS, self.__coord.get_y() - Node.RADIUS))

    def add_neighbour(self, node):
        self.__neighbours.append(node)

    def get_neighbours(self):
        return [n for n in self.__neighbours]

    def show(self):
        self.__show = True

    def hide(self):
        self.__show = False

    def is_showing(self):
        return self.__show

    def get_ID(self):
        return self.__ID

    def set_parent(self, parent_node):
        self.__parent = parent_node

    def get_parent(self):
        return self.__parent

    def set_distance(self, distance):
        self.__distance = distance

    def get_distance(self):
        return self.__distance

    def has_visited(self):
        return self.__visited

    def set_visited(self, visited):
        self.__visited = visited

    def set_debug_colour(self, debug_colour):
        self.__debug_colour = debug_colour

    def get_coord(self):
        return self.__coord


class Graph:
    def __init__(self, width, height):
        self.__width = width
        self.__height = height

        self.__nodes = []

    def __str__(self):
        print(self.__nodes)

    def build_graph(self, temp):
        for y in range(len(temp) - 1):
            for x in range(len(temp[y]) - 1):
                current_node = temp[y][x]

                if current_node not in self.__nodes:
                    self.__nodes.append(current_node)

                    current_node.show()

                possible_pos = [(x, y - 1), (x, y + 1), (x - 1, y), (x + 1, y)]

                for poss_x, poss_y in possible_pos:
                    if 0 <= poss_x < self.__width and 0 <= poss_y < self.__height:
                        current_node.add_neighbour(temp[poss_y][poss_x])

    def draw(self, screen):
        for node in self.__nodes:
            node.draw(screen)

    def breadth_first_search(self, start, waypoint_id):
        if start is None:  # If there isn't a start pos (start of game)
            source_node = self.__nodes[0]
        else:  # There is a start pos
            source_node = start

        for node in self.__nodes:
            node.set_visited(False)
            node.set_distance(0)
            node.set_parent(None)

        source_node.set_distance(0)
        source_node.set_parent(None)

        queue = Queue()
        queue.put(source_node)

        while not queue.empty():
            curr_node = queue.get()

            if curr_node.get_ID() == waypoint_id:
                return curr_node

            for neighbour in curr_node.get_neighbours():
                if not neighbour.has_visited():
                    neighbour.set_visited(True)
                    neighbour.set_distance(curr_node.get_distance() + 1)
                    neighbour.set_parent(curr_node)
                    queue.put(neighbour)
                    # Checking if the node has the id we are searching for
                    if neighbour.get_ID() == waypoint_id:
                        return neighbour

            source_node.set_visited(True)

        return None

    def build_path(self, path, waypoint_id, start, target_waypoint=None):
        if target_waypoint is None:
            # BFS search for path without a target
            target_waypoint = self.breadth_first_search(start, waypoint_id)
        else:
            # BFS search for path with a target
            target_waypoint = self.breadth_first_search(start, target_waypoint.get_ID())


        # Base case: until we reach the start node
        parent = target_waypoint.get_parent()
        if parent is None or target_waypoint.get_ID() == start.get_ID():
            return path

        path.append(parent)  # Push onto stack

        # If debugging then show the path
        if parent.is_showing():
            yellow_path = pygame.Color(255, 248, 14)
            parent.set_debug_colour(yellow_path)

        # Recursive case
        return self.build_path(path, waypoint_id, start, parent)

    def find_nearest_waypoint(self, coord):
        closest_waypoint = None
        closest_distance = None

        for node in self.__nodes:
            distance = node.get_coord().calculate_distance(coord)

            if closest_distance is None:
                closest_waypoint = node
                closest_distance = distance

            elif distance < closest_distance:
                closest_waypoint = node
                closest_distance = distance

        return closest_waypoint

    def __insert_edge(self, source, target):
        source.add_neighbour(target)
        target.insert_neighbour(target)

    def get_nodes(self):
        return self.__nodes
