import math

from litemapy import Schematic, Region, BlockState
import os

# all the different SS-boxes from id=1 to id=15
data_palette = ["minecraft:barrel", "minecraft:white_shulker_box", "minecraft:orange_shulker_box", "minecraft:magenta_shulker_box", "minecraft:light_blue_shulker_box", "minecraft:yellow_shulker_box", "minecraft:lime_shulker_box", "minecraft:pink_shulker_box", "minecraft:gray_shulker_box", "minecraft:light_gray_shulker_box", "minecraft:cyan_shulker_box", "minecraft:purple_shulker_box", "minecraft:blue_shulker_box", "minecraft:brown_shulker_box", "minecraft:green_shulker_box", "minecraft:red_shulker_box"]

placeholder_block = "minecraft:beacon"

point_multiplier = 1

folder_path = None

rom_path = None

pattern_path = None

output_file = None


def to_hex(num, expected):
    hex_num = f"{num:x}"

    # pad with extra zeros to meet expected length
    if len(hex_num) < expected:
        hex_num = "0" * (expected - len(hex_num)) + hex_num

    return hex_num


def end(status):
    input("press any key to exit")
    exit(status)


# this function converts all coords to the coords that would be in a positive size region
def convert_funky_coordinates(coordinates, bounding_box):
    # if a coordinate < 0, subtract its absolute from the bounding box

    corrected_coordinates = [None] * 3

    for i in range(3):
        if bounding_box[i] >= 0:
            corrected_coordinates[i] = coordinates[i]
            continue
        corrected_coordinates[i] = abs(bounding_box[i]) + coordinates[i] - 1

    return tuple(corrected_coordinates)


def schematic_to_3d_array(schematic, filters=None):
    # grab regions (there can only be one)
    schematic_regions = schematic.regions

    # doing this to get the non-enumerable dictionary entry
    for array_region in schematic_regions:
        array_region = schematic_regions[array_region]

        # get dimensions and create array to hold layers
        l, h, w = schematic.length, schematic.height, schematic.width

        schematic_array = [[[0 for z in range(l)] for y in range(h)] for x in range(w)]

        # put every block in the region into the array structure
        for block in array_region.allblockpos():
            x, y, z = block[0], block[1], block[2]
            block_adjusted = convert_funky_coordinates(block, [array_region.width, array_region.height, array_region.length])
            cor_x, cor_y, cor_z = block_adjusted[0], block_adjusted[1], block_adjusted[2]
            # block-id returns a string with quotes in it, so we have to remove it
            block_id = array_region.getblock(x, y, z).blockid.replace("\"", "")
            if filters is None or block_id in filters:
                schematic_array[cor_x][cor_y][cor_z] = block_id

        return schematic_array


def generate_block_palette(schematic_path, y = None):
    # grab schematic from file
    schematic = Schematic.load(schematic_path)

    pattern_region = schematic.regions
    for region_name in pattern_region:
        pattern_region = pattern_region[region_name]
        break

    # convert y value to value inside region
    if pattern_region.height < 0:
        y = pattern_region.height + y + 1

    palette = []

    all_block_pos = pattern_region.allblockpos()
    for block_pos in all_block_pos:
        # add block to palette if not present and y value matches

        # once again, .blockid returns a string with quotation marks, so I have to remove them
        block_id = pattern_region.getblock(block_pos[0], block_pos[1], block_pos[2]).blockid.replace("\"", "")

        if block_id not in palette and (block_pos[1] is y or y is None):
            palette.append(block_id)

    return palette


def generate_block_palette_region(palette, y, expected):
    # generate new region with correct size from table
    palette_region = Region(0, y * point_multiplier, 1 - expected, len(palette), 1, 1 + expected)

    # place block in the schematic next to appropriate data block
    for x in range(len(palette)):
        palette_region.setblock(x, 0, 0, BlockState(palette[x]))

        block_id = to_hex(x + 1, expected)

        for sub_y in range(expected):
            palette_region.setblock(x, 0, sub_y + 1, BlockState(data_palette[int(block_id[sub_y])]))

    return palette_region


def extract_data_points(path, inverted=False):
    rom_schem = Schematic.load(path)
    schematic_3d = schematic_to_3d_array(rom_schem, [placeholder_block])

    data_points = [[[]]]

    if inverted is False:
        layers = []
        for x in range(len(schematic_3d)):
            layer = []
            for y in range(len(schematic_3d[0])):
                line = []
                for z in range(len(schematic_3d[0][0])):
                    block_id = schematic_3d[x][y][z]
                    if block_id == placeholder_block:
                        line.append([x, y, z])
                if line:
                    layer.append(line)
            if layer:
                layers.append(layer)
        return layers

    # write into temporary layer with swapped x/z
    temp_layers = []
    for z in range(len(schematic_3d[0][0])):
        layer = []
        for y in range(len(schematic_3d[0])):
            line = []
            for x in range(len(schematic_3d)):
                block_id = schematic_3d[x][y][z]
                if block_id == placeholder_block:
                    line.append([x, y, z])
            if line:
                layer.append(line)
        if layer:
            temp_layers.append(layer)

        # return  temp_layers

    # swap x and z again to produce standardized output
    layers = schematic_array = [[[0 for z in range(len(temp_layers))] for y in range(len(temp_layers[0]))] for x in range(len(temp_layers[0][0]))]

    for x in range(len(temp_layers)):
        layer = []
        for y in range(len(temp_layers[0])):
            line = []
            for z in range(len(temp_layers[0][0])):
                layers[z][y][x] = temp_layers[x][y][z]

    return layers


def input_path(pre_path, path_name, extension=""):
    # this should repeat until the user inputs a valid file path
    path = pre_path + input(path_name) + extension
    print(path)

    if not os.path.exists(path):
        print(f"invalid file path {path}")
        return input_path(pre_path, path_name, extension)

    return path


# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    if not folder_path:
        folder_path = input_path("", "litematic folder path: ") + "\\"

    if not rom_path:
        rom_path = input_path(folder_path, "ROM litematic name (e.g. \"CoolRom\"): ", ".litematic")

    if not pattern_path:
        pattern_path = input_path(folder_path, "Pattern litematic name (e.g. \"CoolPattern\"): ", ".litematic")

    if not output_file:
        output_file = input("output file name (e.g. \"CoolConfiguredRom\"): ") + ".litematic"

    while True:
        point_multiplier_str = input("block id hexits: ")
        try:
            point_multiplier = int(point_multiplier_str)
            break
        except:
            print(f"could not convert \"{point_multiplier_str}\": not an integer")

    placeholder_input = input("enter placeholder block id or skip to use default (\"minecraft:beacon\"): ")
    if placeholder_input != "":
        placeholder_block = placeholder_input
        print(f"using custom block \"{placeholder_block}\"")
    else:
        print(f"using default block \"{placeholder_block}\"")

    litematic_version = input("enter litematic version (1-6): ")
    print(f"using litematic version {litematic_version}")

    # break pattern schematic down into comparable units
    pattern = schematic_to_3d_array(Schematic.load(pattern_path))

    # attempt to get data Points on z-axis
    dataPoints = extract_data_points(rom_path)

    if not dataPoints:
        print(f"unable to get data points: none found using filter \"{placeholder_block}\"")
        end(1)

    # retry getting data points on x-axis if layout doesn't match up
    if len(dataPoints) is not len(pattern) or len(dataPoints[0]) is not len(pattern[0]*point_multiplier) or len(dataPoints[0][0]) is not len(pattern[0][0]):
        print(f"unable to match data points, retrying on second axis -> pattern({len(pattern)}|{len(pattern[0])} * {point_multiplier}|{len(pattern[0][0])}) data-points({len(dataPoints)}|{len(dataPoints[0])}|{len(dataPoints[0][0])})")
        dataPoints = extract_data_points(rom_path, True)

    # quit if data point layout still doesn't match up
        if len(dataPoints) is not len(pattern) or len(dataPoints[0]) is not len(pattern[0]) or len(dataPoints[0][0]) is not len(pattern[0][0]):
            print(f"unable to match data points, check your dimensions -> pattern({len(pattern)}|{len(pattern[0])}|{len(pattern[0][0])}) data-points({len(dataPoints)}|{len(dataPoints[0])}|{len(dataPoints[0][0])})")
            end(1)

    rom_schematic = Schematic.load(rom_path)
    rom_region = None

    # I somehow have to access an element of a non-enumerable data-structure. IK this sucks, but I'm out of ideas
    for region in rom_schematic.regions:
        rom_region = rom_schematic.regions[region]
        break

    generated_region = Region(0, 0, 3, abs(rom_region.width), abs(rom_region.height), abs(rom_region.length))

    # clone EVERYTHING over to the new region because modifying an existing schem is not possible
    all_blocks = rom_region.allblockpos()
    for block in all_blocks:
        new_block = convert_funky_coordinates(block, (rom_region.width, rom_region.height, rom_region.length))
        generated_region.setblock(new_block[0], new_block[1], new_block[2], rom_region.getblock(block[0], block[1], block[2]))

    # accumulate all regions into regions dict
    regions = {}

    for y in range(math.floor(len(dataPoints[0]) / point_multiplier)):
        # get y layer in schematic
        schem_y = dataPoints[0][y][0][1]
        # generate block palette for current layer
        block_palette = generate_block_palette(pattern_path, y)
        # quit if pattern has too many colors
        if len(block_palette) > 15 + (point_multiplier - 1)* 16:
            print(f"too many colors in pattern on layer {y}: counted {len(block_palette)} Maximum of {15 + (point_multiplier - 1)* 16} allowed")
            end(1)

        print(f"palette for layer: {y}")

        for block in block_palette:
            print(f"{block} -> {data_palette[block_palette.index(block)]}")

        palette_region = generate_block_palette_region(block_palette, schem_y, point_multiplier)
        regions[f"palette for layer {y}"] = palette_region

        for x in range(len(dataPoints)):
            for z in range(len(dataPoints[0][0])):
                # assign each block a hex value, start with 1
                block_id = to_hex(block_palette.index(pattern[x][y][z]) + 1, point_multiplier)

                for sub_y in range(point_multiplier):
                    rx, ry, rz = dataPoints[x][y*point_multiplier + sub_y][z]
                    generated_region.setblock(rx, ry, rz, BlockState(data_palette[int(block_id[sub_y], 16)]))

    regions["rom"] = generated_region

    # generate schematic using regions dict
    generated_schematic = Schematic("generated Rom", "UpsideDownFoxxo's schematic Generator", "nothing to see here", regions, litematic_version)
    generated_schematic.save(folder_path+output_file)

    print(f"conversion successful, schematic saved as {folder_path+output_file}")

    end(0)
