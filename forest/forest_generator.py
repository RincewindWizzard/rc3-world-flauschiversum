import json
import itertools
from enum import Enum


class Compass(Enum):
    NORTH = 0
    NORTH_EAST = 1
    EAST = 2
    SOUTH_EAST = 3
    SOUTH = 4
    SOUTH_WEST = 5
    WEST = 6
    NORTH_WEST = 7

    def coords(self):
        return [(0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1)][self.value]

    def diagonals(self):
        return [Compass.NORTH_EAST, Compass.SOUTH_EAST, Compass.SOUTH_WEST, Compass.NORTH_WEST]

    def __reversed__(self):
        return list(Compass)[(self.value + len(Compass) // 2) % len(Compass)]

    def __repr__(self):
        return self.name


COMPASS_MAP = [
    [Compass.NORTH_WEST, Compass.NORTH, Compass.NORTH_EAST],
    [Compass.WEST, None, Compass.EAST],
    [Compass.SOUTH_WEST, Compass.SOUTH, Compass.SOUTH_EAST],
]


def any_tile():
    return tile_of(None, None)


def tile_of(whitelist=None, blacklist=None):
    if whitelist is not None:
        return lambda tile: tile in whitelist
    elif blacklist is not None:
        return lambda tile: tile not in blacklist
    else:
        return lambda tile: True


def except_of(*blacklist):
    return tile_of(None, blacklist)


def one_of(*whitelist):
    return tile_of(whitelist, None)


class Tile(object):
    def __init__(self, id, matchers=tuple([]), name=None, foreground=True):
        self.id = int(id)
        self.name = name
        self.foreground = foreground

        matcher_list = len(Compass) * [any_tile()]
        for compass, matcher in matchers:
            matcher_list[compass.value] = matcher
        self.matchers = matcher_list

    def add_matcher(self, compass, matcher):
        current_matcher = self.matchers[compass.value]

        self.matchers[compass.value] = lambda tile: current_matcher(tile) and matcher(tile)

    def constraint_dict(self, tileset):
        constraints = {}
        for compass in Compass:
            for other in tileset:
                if self.connects_with(compass, other):
                    if not compass in constraints:
                        constraints[compass] = set()
                    constraints[compass].add(other)
        return constraints

    def constraint_map(self, tileset):
        constraint_dict = self.constraint_dict(tileset)
        return [
            [constraint_dict[compass] if compass in constraint_dict else set([self]) for compass in row]
            for row in COMPASS_MAP
        ]

    def connects_with(self, compass, tile):
        if not tile:
            return True
        else:
            return self.matchers[compass.value](tile.id)

    def __repr__(self):
        return "Tile({})".format(self.name if self.name else self.id)


TILE_EMPTY = Tile(0, name="EMPTY")
TILE_FAIL = Tile(1, name='FAIL')


# TILESET = [
#     TILE_EMPTY,
#     Tile(25, name="TILE_TREE_TOP_LEFT", matchers=[(Compass.EAST, one_of(26)), (Compass.SOUTH, one_of(40, 55, 71)), (Compass.SOUTH_EAST, one_of(41, 56)), (Compass.NORTH_EAST, except_of(25, 55))]),
#     Tile(26, name="TILE_TREE_TOP_RIGHT", matchers=[(Compass.WEST, one_of(25)), (Compass.SOUTH, one_of(41, 56, 70)), (Compass.SOUTH_WEST, one_of(40, 55))]),
#
#     Tile(55, name="TILE_TREE_MIDDLE_LEFT", matchers=[(Compass.EAST, one_of(56)), (Compass.NORTH, one_of(25)), (Compass.SOUTH, one_of(40, 55)), (Compass.SOUTH_EAST, except_of(0))]),
#     Tile(56, name="TILE_TREE_MIDDLE_RIGHT", matchers=[(Compass.WEST, one_of(55)), (Compass.NORTH, one_of(26)), (Compass.SOUTH, one_of(41, 56))]),
#
#     Tile(70, name="TILE_TREE_MIDDLE_LEFT_NEXT_EAST",
#          matchers=[(Compass.NORTH, one_of(26)), (Compass.WEST, one_of(40, 71)), (Compass.EAST, one_of(26, 71))]), #(Compass.NORTH_WEST, one_of(25)),
#     Tile(71, name="TILE_TREE_MIDDLE_RIGHT_NEXT_WEST",
#          matchers=[(Compass.NORTH, one_of(25)), (Compass.WEST, one_of(70, 25)), (Compass.EAST, one_of(41, 70)), (Compass.SOUTH, one_of(41))]),
#
#     Tile(40, name="TILE_TREE_BOTTOM_LEFT", matchers=[(Compass.EAST, one_of(41)), (Compass.NORTH, one_of(25, 55))]),
#     Tile(41, name="TILE_TREE_BOTTOM_RIGHT", matchers=[(Compass.WEST, one_of(40)), (Compass.NORTH, one_of(26, 56, 71))]),
# ]

def tree_tileset(*tiles):
    return [
        Tile(tiles[0], name="TILE_TREE_TOP_LEFT", matchers=[
            (Compass.SOUTH, one_of(tiles[2], tiles[6], tiles[5])),
            (Compass.EAST, one_of(tiles[0], tiles[3], tiles[5])),
        ]),
        Tile(tiles[1], name="TILE_TREE_TOP_RIGHT", matchers=[
            (Compass.SOUTH, one_of(tiles[3], tiles[4], tiles[7])),
            (Compass.WEST, one_of(tiles[0], tiles[2], tiles[4])),
        ]),

        Tile(tiles[2], name="TILE_TREE_MIDDLE_LEFT", matchers=[
            (Compass.NORTH, one_of(tiles[0], tiles[2], tiles[4])),
            (Compass.SOUTH, one_of(tiles[6], tiles[2], tiles[5])),
            (Compass.EAST, one_of(tiles[1], tiles[3], tiles[5])),
        ]),
        Tile(tiles[3], name="TILE_TREE_MIDDLE_RIGHT", matchers=[
            (Compass.NORTH, one_of(tiles[1], tiles[3], tiles[5])),
            (Compass.SOUTH, one_of(tiles[7], tiles[3], tiles[4])),
            (Compass.WEST, one_of(tiles[0], tiles[2], tiles[4])),
        ]),

        Tile(tiles[4], name="TILE_TREE_MIDDLE_LEFT_NEXT_EAST", matchers=[
            (Compass.NORTH, one_of(tiles[1], tiles[3], tiles[5])),
            (Compass.SOUTH, one_of(tiles[6], tiles[2], tiles[5])),
            (Compass.EAST, one_of(tiles[1], tiles[3], tiles[5])),
            (Compass.WEST, one_of(tiles[2], tiles[5])),
        ]),
        Tile(tiles[5], name="TILE_TREE_MIDDLE_RIGHT_NEXT_WEST", matchers=[
            (Compass.NORTH, one_of(tiles[0], tiles[2], tiles[4])),
            (Compass.SOUTH, one_of(tiles[7], tiles[3], tiles[4])),
            (Compass.EAST, one_of(tiles[3], tiles[4])),
            (Compass.WEST, one_of(tiles[0], tiles[2], tiles[4])),
        ]),

        Tile(tiles[6], name="TILE_TREE_BOTTOM_LEFT", foreground=False, matchers=[
            (Compass.NORTH, one_of(tiles[0], tiles[2], tiles[4])),
            (Compass.EAST, one_of(tiles[7], tiles[4])),
        ]),
        Tile(tiles[7], name="TILE_TREE_BOTTOM_RIGHT", foreground=False, matchers=[
            (Compass.NORTH, one_of(tiles[1], tiles[3], tiles[5])),
            (Compass.WEST, one_of(tiles[6], tiles[5])),
        ])]


# tree_tileset(25, 26, 55, 56, 70, 71, 40, 41) # Frühlingswald
# tree_tileset(27, 28, 42, 43, 57, 58, 72, 73) # Sommerwald
# tree_tileset(29, 30, 44, 45, 59, 60, 74, 75) # Herbstwald
# tree_tileset(31, 32, 46, 47, 61, 62, 76, 77) # Winterwald


TILESET = [
    TILE_EMPTY
] + tree_tileset(31, 32, 46, 47, 61, 62, 76, 77)
# + [Tile(tid, matchers=[ (compass, one_of(0)) for compass in Compass]) for tid in [85, 86, 87, 88, 89, 90, 100, 101, 102, 103, 104, 105, 106, 107, 115, 116]] # Freistehende Objekte


def generate_map(width, height, tileset, tile_chooser=lambda p: p[0], clearance_map=None, clearance_tile=TILE_EMPTY):
    map_grid = [[None for y in range(height)] for x in range(width)]
    if clearance_map:
        for x in range(width):
            for y in range(height):
                if clearance_map[x][y]:
                    map_grid[x][y] = clearance_tile

    for x in range(width):
        for y in range(height):
            if not map_grid[x][y]:
                possible_tiles = [tile for tile in tileset if can_be_connected(tile, x, y, map_grid)]
                if len(possible_tiles) == 0:
                    # with open('/tmp/map_error.log', 'w') as f:
                    #     f.write(repr(export_map(map_grid)))
                    print('({},{})'.format(x, y))
                    map_grid[x][y] = TILE_FAIL
                    #raise IndexError("No more possible tiles: " + repr(export_map(map_grid)))
                else:
                    choosen_tile = tile_chooser(possible_tiles)
                    map_grid[x][y] = choosen_tile
    return map_grid


def can_be_connected(tile, x, y, map_grid):
    result = True
    for _, compass, other in connected_tiles(x, y, map_grid):
        result &= tile.connects_with(compass, other)
        if other:
            result &= other.connects_with(reversed(compass), tile)
    return result


def tile_combinations(map_grid):
    width = len(map_grid)
    height = len(map_grid[0])

    for x in range(width):
        for y in range(height):
            for value in connected_tiles(x, y, map_grid):
                yield value


def connected_tiles(x, y, map_grid):
    width = len(map_grid)
    height = len(map_grid[0])
    for compass in Compass:
        delta_x, delta_y = compass.coords()
        x1 = x + delta_x
        y1 = y + delta_y
        if x1 < width and y1 < height and x1 >= 0 and y1 >= 0:
            yield (map_grid[x][y], compass, map_grid[x1][y1])


def is_map_valid(map_grid):
    result = True
    for tile, compass, other in tile_combinations(map_grid):
        result &= tile.connects_with(compass, other)
    return result


def export_map(map_grid):
    map_grid = flip(map_grid)
    width = len(map_grid)
    height = len(map_grid[0])
    return [(map_grid[x][y].id if map_grid[x][y] else 0) for x, y in itertools.product(range(width), range(height))]


def insert_into_tiled_json(map_grid, path, layername):
    doc = json.load(open(path, 'r'))

    map_grid_foreground = [[(tile if tile.foreground else TILE_EMPTY) for tile in row] for row in map_grid]
    map_grid_background = [[(tile if not tile.foreground else TILE_EMPTY) for tile in row] for row in map_grid]

    for layer in doc['layers']:
        if layer['name'] == layername + '_foreground':
            layer['data'] = export_map(map_grid_foreground)
        elif layer['name'] == layername + '_background':
            layer['data'] = export_map(map_grid_background)

    json.dump(doc, open(path, 'w'))


def load_layer_from_tiled_json(path, layername):
    doc = json.load(open(path, 'r'))
    width = int(doc['width'])
    height = int(doc['height'])
    for layer in doc['layers']:
        if layer['name'] == layername:
            return flip([[layer['data'][x + y * width] for x in range(width)] for y in range(height)])


def flip(matrix):
    return [[matrix[y][x] for y in range(len(matrix))] for x in range(len(matrix[0]))]

# def connectable(tile1, compass, tile2):
#     return tile1.connects_with(compass, tile2) and tile2.connects_with(reversed(compass), tile1)
#
# def possible_middleman_exists(tile1, compass, tile2, tileset):
#     if compass == Compass.NORTH_EAST:
#         return not len([pivot for pivot in tileset if
#                         connectable(tile1, Compass.NORTH, pivot) and connectable(tile2, Compass.WEST, pivot)]) == 0
#     elif compass == Compass.NORTH_EAST:
#         return not len([pivot for pivot in tileset if connectable(tile1, Compass.NORTH, pivot) and connectable(tile2, Compass.WEST, pivot)]) == 0
#     elif compass == Compass.NORTH_WEST:
#         return not len([pivot for pivot in tileset if connectable(tile1, Compass.NORTH, pivot) and connectable(tile2, Compass.WEST, pivot)]) == 0
#     elif compass == Compass.NORTH_EAST:
#         return not len([pivot for pivot in tileset if connectable(tile1, Compass.NORTH, pivot) and connectable(tile2, Compass.WEST, pivot)]) == 0
#
# def infer_constraints(tile1, tile2, tileset):
#     """
#     * Wenn zwei Tiles nebeneinander platziert, kann es sein, dass es kein Tile mehr im Tileset gibt, dass dazwischen passen würde.
#     * Daraus lassen sich weitere Regeln schließen, die aus den bereits vorhandenen hervorgehen.
#     """
#     for compass in Compass.diagonals():
#         # wenn sich kein tile zur Verbindung findet, dann haben wir ein neues Constraint
#         if compass == Compass.NORTH_EAST:
#                 if len([pivot for pivot in tileset if connectable(tile1, Compass.NORTH, pivot) and connectable(tile2, Compass.WEST, pivot)]) == 0:
#                     tile1.add_matcher(compass, except_of(tile2.id))
#                     tile2.add_matcher(reversed(compass), except_of(tile1.id))
#
#     if tile1.connects_with
