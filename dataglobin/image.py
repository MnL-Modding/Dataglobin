import struct
from io import BytesIO
from math import prod, ceil
from PySide6 import QtCore, QtGui, QtWidgets
from PIL import Image, ImageOps
from PIL.ImageQt import ImageQt
from mnllib.bis import decompress

SIZING_TABLE = [[(8, 8), (16, 16), (32, 32), (64, 64)], [(16, 8), (32, 8), (32, 16), (64, 32)], [(8, 16), (8, 32), (16, 32), (32, 64)]]

def create_sprite(table_offsets, overlays, Obj_file, group_num, anim_num, sprite_type, lang = 0):
    if isinstance(anim_num, int):
        anim_list = [anim_num]
    else:
        anim_list = list(anim_num)

    if isinstance(overlays, list):
        return create_XObj_sprite(table_offsets, overlays[0], overlays[1], Obj_file, group_num, anim_list, lang, sprite_type)
    else:
        return create_XObj_sprite(table_offsets, overlays, overlays, Obj_file, group_num, anim_list, lang, sprite_type)

def create_XObj_sprite(table_offsets, file_data_overlay, group_data_overlay, XObj_file, group_num, anim_list, lang, sprite_type):
    file_data_overlay = BytesIO(file_data_overlay)
    group_data_overlay = BytesIO(group_data_overlay)
    XObj_file = BytesIO(XObj_file)

    # ==================================================================
    # start reading the data

    group_data_overlay.seek(table_offsets[1] + (group_num * [8, 24, 10, 10][sprite_type])) # get sprite group data
    anim_id, graph_id, pal_gid, use_lang = struct.unpack('<3H2xH', group_data_overlay.read(10))

    if sprite_type == 0:
        use_lang = 0
    elif sprite_type == 1:
        use_lang = 0
        shadow_type = int.from_bytes(group_data_overlay.read(1))

    if use_lang & 1 != 0: # check if current sprite group uses languages
        group_data_overlay.seek(table_offsets[1] + ((group_num + lang) * [8, 24, 10, 10][sprite_type])) # get sprite group data again
        anim_id, graph_id, pal_gid = struct.unpack('<3H', group_data_overlay.read(6))
    
    group_data_overlay.seek(table_offsets[2] + (pal_gid * 4))
    pal_id = int.from_bytes(group_data_overlay.read(2), "little")

    file_data_overlay.seek(table_offsets[0] + (anim_id * 4) + 4)
    XObj_file.seek(int.from_bytes(file_data_overlay.read(4), "little"))
    animation_file = BytesIO(decompress(XObj_file))

    file_data_overlay.seek(table_offsets[0] + (graph_id * 4) + 4)
    XObj_file.seek(int.from_bytes(file_data_overlay.read(4), "little"))
    graphics_buffer = BytesIO(decompress(XObj_file))

    file_data_overlay.seek(table_offsets[0] + (pal_id * 4) + 4)
    XObj_file.seek(int.from_bytes(file_data_overlay.read(4), "little"))
    palette_file_size = int.from_bytes(XObj_file.read(4), "little")
    palette_file = define_palette(struct.unpack(f'<{palette_file_size // 2}H', XObj_file.read(palette_file_size)))

    # ==================================================================
    # start interpreting the data

    _settings_byte, anims_table, parts_table, affine_table, tex_shift, graph_offset_table = struct.unpack('<2xBx3I5xB2xI', animation_file.read(0x1C))
    sprite_mode = _settings_byte & 3
    swizzle_flag = (_settings_byte >> 3) & 1 == 0

    img = Image.new("RGBA", (256, 256))

    for i in range(len(anim_list)):
        anim_num = anim_list[i]

        animation_file.seek(anims_table + (anim_num * 8))
        frame_offset = int.from_bytes(animation_file.read(2), "little")

        animation_file.seek(frame_offset)
        part_list_offset, part_amt, matrix_id = struct.unpack('<HxB2xH', animation_file.read(8))

        # ==================================================================
        # start assembling the sprite

        if part_amt == 0 and len(anim_list) == 1:
            if sprite_type != 1:
                return QtGui.QPixmap(QtGui.QImage(ImageQt(Image.new("RGBA", (16, 16)))))
            else:
                return QtGui.QPixmap(QtGui.QImage(ImageQt(Image.new("RGBA", (16, 16))))), shadow_type

        for i in reversed(range(part_amt)):
            animation_file.seek(parts_table + ((part_list_offset + i) * 8))
            oam_settings, part_x, part_y = struct.unpack('<I2h', animation_file.read(8))

            part_xy = SIZING_TABLE[(oam_settings >> 6) & 0b11][(oam_settings >> 10) & 0b11]

            pal_shift = (oam_settings >> 14) & 0b1111

            animation_file.seek(graph_offset_table + ((part_list_offset + i) * 2))
            graphics_buffer.seek((int.from_bytes(animation_file.read(2), "little") << tex_shift) + 4)
            buffer_in = graphics_buffer.read(prod(part_xy))

            img_part = create_sprite_part(
                buffer_in,
                palette_file,
                part_xy,
                sprite_mode,
                pal_shift,
                swizzle_flag
            )

            rot_scale_flag = (oam_settings >>  0) & 0x01 != 0
            x_flip         = (oam_settings >>  8) & 0x01 != 0
            y_flip         = (oam_settings >>  9) & 0x01 != 0
            part_matrix_id = (oam_settings >> 18) & 0x3F

            if x_flip:
                img_part = ImageOps.mirror(img_part)
            if y_flip:
                img_part = ImageOps.flip(img_part)

            sprite_part_x_center = part_x + (img.width // 2)
            sprite_part_y_center = part_y + (img.height // 2)
            sprite_part_x_offset = sprite_part_x_center - (part_xy[0] // 2)
            sprite_part_y_offset = sprite_part_y_center - (part_xy[1] // 2)
            
            if rot_scale_flag:
                animation_file.seek(affine_table + (part_matrix_id * 8))

                matrix = calculate_from_matrix(animation_file.read(8), (-sprite_part_x_center, -sprite_part_y_center), 1)

                img_matrix = Image.new("RGBA", img.size)
                img_matrix.paste(img_part, (sprite_part_x_offset, sprite_part_y_offset), img_part)
                img_matrix = img_matrix.transform(img_matrix.size, Image.AFFINE, matrix)

                img.paste(img_matrix, (0, 0), img_matrix)
            else:
                img.paste(img_part, (sprite_part_x_offset, sprite_part_y_offset), img_part)
        
        if matrix_id != 0:
            animation_file.seek(affine_table + ((matrix_id - 1) * 12))
            matrix = calculate_from_matrix(animation_file.read(12), (-img.width // 2, -img.height // 2))
            img = img.transform(img.size, Image.AFFINE, matrix)
    
    if sprite_type != 1:
        return_values = QtGui.QPixmap(QtGui.QImage(ImageQt(img)))
    else:
        return_values = QtGui.QPixmap(QtGui.QImage(ImageQt(img))), shadow_type

    return return_values

# mode 0 is 2D, mode 1 is 3D
def define_palette(current_pal, mode = 1):
    out_pal = []
    for color_raw in current_pal:
        return_color = []
        for i in range(3):
            x = color_raw >> (i * 5) & 0x1F               # 15 bit color
            x = (x << 1) + min(x, mode)                   # 18 bit color
            return_color.append((x << 2) | (x >> 4))      # 24 bit color
        out_pal.append(return_color)
    return out_pal

def create_sprite_part(buffer_in, current_pal, part_xy, sprite_mode, pal_shift, swizzle, transparent_flag = True):
    pal_shift *= 16
    if (swizzle):
        part_size = 8 * 8
        tiles = (part_xy[0] * part_xy[1]) // 64
        tile_x, tile_y = 8, 8
    else:
        part_size = part_xy[0] * part_xy[1]
        tile_x, tile_y = part_xy[0], part_xy[1]
        tiles = 1
    img_out = Image.new("RGBA", (part_xy[0], part_xy[1]))
    for t in range(tiles):
        buffer_out = bytearray()
        match (sprite_mode):
            case 0:
                # 8bpp bitmap
                for i in range(part_size):
                    current_pixel = buffer_in[(t * 64) + i]
                    if current_pixel + pal_shift < len(current_pal):
                        buffer_out.extend(current_pal[current_pixel + pal_shift])
                    else:
                        buffer_out.extend([0, 0, 0])
                    # transparency
                    if transparent_flag:
                        if (current_pixel == 0): buffer_out.append(0x00)
                        else: buffer_out.append(0xFF)
                    else:
                        buffer_out.append(0xFF)
            case 1:
                # AI35
                for i in range(part_size):
                    current_pixel = buffer_in[(t * 64) + i] & 0b11111
                    if current_pixel + pal_shift < len(current_pal):
                        buffer_out.extend(current_pal[current_pixel + pal_shift])
                    else:
                        buffer_out.extend([0, 0, 0])
                    # transparency
                    if transparent_flag:
                        alpha = ceil(0xFF * ((buffer_in[(t * 64) + i] >> 5) / 7))
                        buffer_out.append(alpha)
                    else:
                        buffer_out.append(0xFF)
            case 2:
                # AI53
                for i in range(part_size):
                    current_pixel = buffer_in[(t * 64) + i] & 0b111
                    if current_pixel + pal_shift < len(current_pal):
                        buffer_out.extend(current_pal[current_pixel + pal_shift])
                    else:
                        buffer_out.extend([0, 0, 0])
                    # transparency
                    if transparent_flag:
                        alpha = buffer_in[(t * 64) + i] >> 3
                        alpha = (alpha << 3) | (alpha >> 2)
                        buffer_out.append(alpha)
                    else:
                        buffer_out.append(0xFF)
            case 3:
                # 4bpp bitmap
                for i in range(part_size):
                    current_pixel = (buffer_in[((t * 64) + i) // 2] >> ((i % 2) * 4)) & 0b1111
                    if current_pixel + pal_shift < len(current_pal):
                        buffer_out.extend(current_pal[current_pixel + pal_shift])
                    else:
                        buffer_out.extend([0, 0, 0])
                    # transparency
                    if transparent_flag:
                        if (current_pixel == 0): buffer_out.append(0x00)
                        else: buffer_out.append(0xFF)
                    else:
                        buffer_out.append(0xFF)
        # swizzle (if swizzle is disabled, x and y offset will always just be 0 and the image will display normally)
        x = (t % (part_xy[0] // tile_x)) * 8
        y = (t // (part_xy[0] // tile_x)) * 8
        img_out.paste(Image.frombytes("RGBA", (tile_x, tile_y), buffer_out), (x, y))
    return img_out

def calculate_from_matrix(buffer_in, center, matrix_type = 0):
    out = [1, 0, 0, 0, 1, 0]
    match matrix_type:
        case 0:
            out[0], out[3], out[1], out[4], out[2], out[5] = struct.unpack('<hhhhhh', buffer_in)
        case 1:
            out[0], out[3], out[1], out[4] = struct.unpack('<hhhh', buffer_in)
    for i in range(6):
        if (i != 2 and i != 5):
            out[i] /= 0x100

    new_center = center[0] - out[2], center[1] - out[5]
    dt = out[0] * out[4] - out[1] * out[3]
    new_out = out.copy()
    new_out[0] = out[4] / dt
    new_out[4] = out[0] / dt
    new_out[1] = -out[1] / dt
    new_out[3] = -out[3] / dt
    match matrix_type:
        case 0:
            new_out[2] = (new_center[0] * new_out[0]) + (new_center[1] * new_out[1]) - center[0]
            new_out[5] = (new_center[0] * new_out[3]) + (new_center[1] * new_out[4]) - center[1]
        case 1:
            new_out[2] = (center[0] * new_out[0]) + (center[1] * new_out[1]) - center[0]
            new_out[5] = (center[0] * new_out[3]) + (center[1] * new_out[4]) - center[1]
    return new_out

def image_crop(image_to_crop):
    qimg = image_to_crop.toImage()
    buffer = QtCore.QBuffer()
    buffer.open(QtCore.QBuffer.ReadWrite)
    qimg.save(buffer, "PNG")
    img = Image.open(BytesIO(buffer.data()))
    img = img.crop(img.getbbox())
    return QtGui.QPixmap(QtGui.QImage(ImageQt(img)))