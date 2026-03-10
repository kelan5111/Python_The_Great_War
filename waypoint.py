import pygame
from queue import Queue

from coordinate import Coordinate


class Node:
    RADIUS = 5
    next_id = 0

    def __init__(self, coord):
        self._neighbours = []

        self._ID = Node.next_id + 1
        self._coord = coord
        self._show = False
        self._debug_colour = (128, 255, 0)

        self._visited = False
        self._distance = 0
        self._parent = None

        Node.next_id += 1

    def __repr__(self):
        return f'Node ID: {self._ID}'

    def draw(self, screen, camera):
        screen_coord = camera.translate_coord(self._coord.get_coord())
        pygame.draw.circle(screen, self._debug_colour, screen_coord, Node.RADIUS)

    def add_neighbour(self, node):
        self._neighbours.append(node)

    def get_neighbours(self):
        return [n for n in self._neighbours]

    def show(self):
        self._show = True

    def hide(self):
        self._show = False

    def is_showing(self):
        return self._show

    def get_ID(self):
        return self._ID

    def set_parent(self, parent_node):
        self._parent = parent_node

    def get_parent(self):
        return self._parent

    def set_distance(self, distance):
        self._distance = distance

    def get_distance(self):
        return self._distance

    def has_visited(self):
        return self._visited

    def set_visited(self, visited):
        self._visited = visited

    def set_debug_colour(self, debug_colour):
        self._debug_colour = debug_colour

    def get_coord(self):
        return self._coord


class Graph:
    def __init__(self, width=None, height=None, spaced=None):
        self._width = width
        self._height = height
        self._spaced = spaced

        self._debug = False

        self._nodes = []

    def __str__(self):
        return "Graph"

    def build(self, width_coord=None, height_coord=None):
        temp = []
        start_width_x = 0
        start_height_x = 0

        if width_coord is not None and height_coord is not None:
            start_width_x = width_coord[0]
            self._width = width_coord[1]
            start_height_x = height_coord[0]
            self._height = height_coord[1]

        for x in range(start_width_x, self._width, self._spaced):
            column = []  # Create a new empty column for every X
            for y in range(start_height_x, self._height, self._spaced):
                column.append(Node(Coordinate(x + self._spaced, y + self._spaced)))  # Add nodes to the column
            temp.append(column)

        # Building the graph
        self._build_graph(temp)

    def _build_graph(self, temp):
        for col in range(len(temp)):
            for row in range(len(temp[col])):
                current_node = temp[col][row]

                if current_node not in self._nodes:
                    self._nodes.append(current_node)
                    current_node.show()

                possible_pos = [(col, row - 1), (col, row + 1), (col - 1, row), (col + 1, row)]

                for poss_col, poss_row in possible_pos:
                    if 0 <= poss_col < len(temp) and 0 <= poss_row < len(temp[poss_col]):
                        current_node.add_neighbour(temp[poss_col][poss_row])

    def draw(self, screen, camera):
        if self._debug:
            for node in self._nodes:
                node.draw(screen, camera)

    def _breadth_first_search(self, start, waypoint_id):
        if start is None:  # If there isn't a start pos (start of game)
            source_node = self._nodes[0]
        else:  # There is a start pos
            source_node = start

        for node in self._nodes:
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
        if len(path) == 0:
            if target_waypoint is None:
                # BFS search for path without a target
                target_waypoint = self._breadth_first_search(start, waypoint_id)
            else:
                # BFS search for path with a target
                target_waypoint = self._breadth_first_search(start, target_waypoint.get_ID())

        # Base case: until we reach the start node
        parent = target_waypoint.get_parent()
        if parent is None or target_waypoint.get_ID() == start.get_ID():
            return path

        path.append(parent)  # Push onto stack

        # Recursive case
        return self.build_path(path, waypoint_id, start, parent)

    def find_nearest_waypoint(self, coord):
        closest_waypoint = None
        closest_distance = None

        for node in self._nodes:
            distance = node.get_coord().calculate_distance(coord)

            if closest_distance is None:
                closest_waypoint = node
                closest_distance = distance

            elif distance < closest_distance:
                closest_waypoint = node
                closest_distance = distance

        return closest_waypoint

    def set_debug(self, debug=False):
        self._debug = debug

    def get_nodes(self):
        return self._nodes
