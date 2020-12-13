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
    def __init__(self, id, matchers=tuple([]), name=None):
        self.id = int(id)
        self.name = name

        matcher_list = len(Compass) * [ any_tile() ]
        for compass, matcher in matchers:
            matcher_list[compass.value] = matcher
        self.matchers = matcher_list

    def add_matcher(self, compass, matcher):
        current_matcher = self.matchers[compass.value]

        self.matchers[compass.value] = lambda tile: current_matcher(tile) and matcher(tile)

    def connects_with(self, compass, tile):
        if not tile:
            return True
        else:
            return self.matchers[compass.value](tile.id)

    def __repr__(self):
        return "Tile({})".format(self.name if self.name else self.id)



TILE_EMPTY = Tile(0, name="EMPTY")
TILESET = [
    TILE_EMPTY,
    Tile(25, name="TILE_TREE_TOP_LEFT", matchers=[(Compass.EAST, one_of(26)), (Compass.SOUTH, one_of(40, 55)), (Compass.SOUTH_EAST, one_of(41, 56)), (Compass.NORTH_EAST, except_of(25, 55))]),
    Tile(26, name="TILE_TREE_TOP_RIGHT", matchers=[(Compass.WEST, one_of(25)), (Compass.SOUTH, one_of(41, 56)), (Compass.SOUTH_WEST, one_of(40, 55))]),

    Tile(55, name="TILE_TREE_MIDDLE_LEFT", matchers=[(Compass.EAST, one_of(56)), (Compass.NORTH, one_of(25)), (Compass.SOUTH, one_of(40, 55)), (Compass.SOUTH_EAST, except_of(0))]),
    Tile(56, name="TILE_TREE_MIDDLE_RIGHT", matchers=[(Compass.WEST, one_of(55)), (Compass.NORTH, one_of(26)), (Compass.SOUTH, one_of(41, 56))]),

    Tile(40, name="TILE_TREE_BOTTOM_LEFT", matchers=[(Compass.EAST, one_of(41)), (Compass.NORTH, one_of(25, 55))]),
    Tile(41, name="TILE_TREE_BOTTOM_RIGHT", matchers=[(Compass.WEST, one_of(40)), (Compass.NORTH, one_of(26, 56))]),
]



def generate_map(width, height, tileset, tile_chooser=lambda p: p[0], clearance_map=None, clearance_tile=TILE_EMPTY):
    map_grid =  [[None for y in range(height)] for x in range(width)]
    if clearance_map:
        for x in range(width):
            for y in range(height):
                if clearance_map[x][y]:
                    map_grid[x][y] = clearance_tile

    try:
        for x in range(width):
            for y in range(height):
                if not map_grid[x][y]:
                    possible_tiles = [ tile for tile in tileset if can_be_connected(tile, x, y, map_grid) ]
                    if len(possible_tiles) == 0:
                        # with open('/tmp/map_error.log', 'w') as f:
                        #     f.write(repr(export_map(map_grid)))
                        raise IndexError("No more possible tiles: " + repr(export_map(map_grid)))
                    else:
                        choosen_tile = tile_chooser(possible_tiles)
                        map_grid[x][y] = choosen_tile

    except:
        print("ERROR!")

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
    for layer in doc['layers']:
        if layer['name'] == layername:
            layer['data'] = export_map(map_grid)

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



