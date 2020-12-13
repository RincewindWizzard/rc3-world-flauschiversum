import unittest
from forest.forest_generator import *
import random
from pprint import pprint


def print_constraint_map(constraints):
    constraint_map = [
        [{tile.id for tile in cell} for cell in row]
        for row in constraints
    ]
    pprint(constraint_map)



class TileConstraintTest(unittest.TestCase):
    def test_tiles(self):
        tile_a = Tile(1, matchers=[(compass, one_of(2)) for compass in Compass])
        tile_b = Tile(2, matchers=[(compass, one_of(1)) for compass in Compass])

        self.assertTrue(tile_a.connects_with(Compass.WEST, tile_b))
        self.assertFalse(tile_a.connects_with(Compass.WEST, tile_a))

    def test_one_of(self):
        self.assertTrue(one_of(1)(1))
        self.assertFalse(one_of(1)(2))

    def test_except_of(self):
        self.assertTrue(except_of(1)(2))
        self.assertFalse(except_of(1)(1))

    def test_constraint_inference(self):
        tile_a = Tile(1, matchers=[(Compass.SOUTH, one_of(2))])
        tile_b = Tile(2, matchers=[(Compass.EAST, one_of(3))])
        tile_c = Tile(3)

        tileset = {tile_a, tile_b, tile_c}

        cmap = tile_a.constraint_map(tileset)

        print_constraint_map(cmap)



    def test_map_generate_3_1(self):
        tile_1 = Tile(1, matchers=[(Compass.EAST, one_of(2))])
        tile_2 = Tile(2, matchers=[(Compass.EAST, one_of(1))])

        map_grid = generate_map(3, 1, [tile_1, tile_2])
        print(map_grid)

    def test_map_generate_3_3(self):
        tile_1 = Tile(1, matchers=[(compass, one_of(2, 3, 4)) for compass in Compass])
        tile_2 = Tile(2, matchers=[(compass, one_of(1, 3, 4)) for compass in Compass])
        tile_3 = Tile(3, matchers=[(compass, one_of(2, 1, 4)) for compass in Compass])
        tile_4 = Tile(4, matchers=[(compass, one_of(1, 2, 3)) for compass in Compass])

        map_grid = generate_map(3, 3, [tile_1, tile_2, tile_3, tile_4])

        print(map_grid)

        for tile, compass, other in tile_combinations(map_grid):
            self.assertTrue(tile.connects_with(compass, other), msg="{} does not connect {} with {}".format(tile, compass.name, other))

    def test_compass(self):
        self.assertEqual(Compass.EAST, reversed(Compass.WEST))

        for compass in Compass:
            x, y = compass.coords()
            x1, y1 = reversed(compass).coords()

            self.assertEqual(0, x + x1)
            self.assertEqual(0, y + y1)

    def test_connected_tiles(self):
        width = 3
        height = 3

        map_grid =  [[(x,y) for y in range(height)] for x in range(width)]
        for a, compass, b in connected_tiles(1, 1, map_grid):
            self.assertEqual(a[0] + compass.coords()[0], b[0])
            self.assertEqual(a[1] + compass.coords()[1], b[1])

        self.assertEqual(5, len([a for _, _, a in connected_tiles(0, 1, map_grid)]))

    def test_simple_tree(self):
        map_grid = flip([
            [TILE_EMPTY, TILE_EMPTY, TILE_EMPTY, TILE_EMPTY],
            [TILE_EMPTY, TILE_TREE_TOP_LEFT, TILE_TREE_TOP_RIGHT, TILE_EMPTY],
            [TILE_EMPTY, TILE_TREE_BOTTOM_LEFT, TILE_TREE_BOTTOM_RIGHT, TILE_EMPTY],
            [TILE_EMPTY, TILE_EMPTY, TILE_EMPTY, TILE_EMPTY],
        ])
        self.assertTrue(is_map_valid(map_grid))

        exported = export_map(map_grid)
        print(exported)

    def test_generate_simple_forest(self):
        width = 300
        height = 300
        random.seed(0)

        weights = {
            0: 3
        }

        def tile_chooser(possbile_tiles):
            return random.choices(possbile_tiles, weights=[(weights[tile.id] if tile.id in weights else 1) for tile in possbile_tiles])[0]

        map_grid = generate_map(width, height, TILESET, tile_chooser=tile_chooser)
        insert_into_tiled_json(map_grid, 'forest.json', 'forest_generated')

    def test_generate_simple_forest_with_pathways(self):
        width = 100
        height = 100
        random.seed(0)

        tile_chooser = lambda p: random.choices(p, weights=[(100 if tile.id == 0 else 1) for tile in p])

        forest_pathways = load_layer_from_tiled_json('forest.json', 'forest_pathway')
        map_grid = generate_map(width, height, TILESET, tile_chooser=tile_chooser, clearance_map=forest_pathways, clearance_tile=TILE_EMPTY)
        insert_into_tiled_json(map_grid, 'forest.json', 'forest_generated')

    def test_load_layer_from_tiled_json(self):
        forest_pathways = load_layer_from_tiled_json('forest.json', 'forest_pathway')
        self.assertEqual(10, forest_pathways[0][3])
        self.assertEqual(0, forest_pathways[99][99])

        print(forest_pathways)

    def test_change_season_summer(self):
        replacements = {
            25: 27,
            26: 28,
            55: 57,
            56: 58,
            70: 72,
            71: 73,
            40: 42,
            41: 43
        }

        map_grid_foreground = load_layer_from_tiled_json_raw('forest.json', 'forest_spring_foreground')
        map_grid_background = load_layer_from_tiled_json_raw('forest.json', 'forest_spring_background')

        map_grid_foreground = [(replacements[x] if x in replacements else x) for x in map_grid_foreground]
        map_grid_background = [(replacements[x] if x in replacements else x) for x in map_grid_background]

        write_layer_into_tiled_json('forest.json', 'forest_summer_foreground', map_grid_foreground)
        write_layer_into_tiled_json('forest.json', 'forest_summer_background', map_grid_background)

    def test_change_season_winter(self):
        replacements = {
            25: 31,
            26: 32,
            55: 61,
            56: 62,
            70: 76,
            71: 77,
            40: 46,
            41: 47
        }

        map_grid_foreground = load_layer_from_tiled_json_raw('forest.json', 'forest_spring_foreground')
        map_grid_background = load_layer_from_tiled_json_raw('forest.json', 'forest_spring_background')

        map_grid_foreground = [(replacements[x] if x in replacements else x) for x in map_grid_foreground]
        map_grid_background = [(replacements[x] if x in replacements else x) for x in map_grid_background]

        write_layer_into_tiled_json('forest.json', 'forest_winter_foreground', map_grid_foreground)
        write_layer_into_tiled_json('forest.json', 'forest_winter_background', map_grid_background)

    def test_change_season_autumn(self):
        replacements = {
            25: 29,
            26: 30,
            55: 59,
            56: 60,
            70: 74,
            71: 75,
            40: 44,
            41: 45
        }

        map_grid_foreground = load_layer_from_tiled_json_raw('forest.json', 'forest_spring_foreground')
        map_grid_background = load_layer_from_tiled_json_raw('forest.json', 'forest_spring_background')

        map_grid_foreground = [(replacements[x] if x in replacements else x) for x in map_grid_foreground]
        map_grid_background = [(replacements[x] if x in replacements else x) for x in map_grid_background]

        write_layer_into_tiled_json('forest.json', 'forest_autumn_foreground', map_grid_foreground)
        write_layer_into_tiled_json('forest.json', 'forest_autumn_background', map_grid_background)



if __name__ == '__main__':
    unittest.main()
