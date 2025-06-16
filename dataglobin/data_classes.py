import struct

class EnemyData:
    def __init__(self, input_data):
        data = struct.unpack('<2HIxBh3HI6H2x', input_data)

        self.name      = data[0x0]
        self.script    = data[0x1]
        self.obj_id    = data[0x2]

        self.level     = data[0x3] # cap at 99
        self.HP        = data[0x4] # seemingly no cap
        self.POW       = data[0x5] # cap at 999
        self.DEF       = data[0x6] # cap at 999
        self.SPEED     = data[0x7] # cap at 999

        self.is_spiked = data[0x8] & 0x00000001 != 0
        self.is_flying = data[0x8] & 0x00000004 != 0

        self.fire_damage  = (data[0x8] >>  3) & 0b11
        self.burn_chance  = (data[0x8] >>  8) & 0b11
        self.dizzy_chance = (data[0x8] >> 10) & 0b11
        self.stat_chance  = (data[0x8] >> 12) & 0b11
        self.insta_chance = (data[0x8] >> 14) & 0b11

        self.unk0      = data[0x8] & 0x00010000 != 0
        self.unk1      = data[0x8] & 0x00020000 != 0

        self.EXP       = data[0x9] # cap at 9999
        self.coins     = data[0xA] # cap at 9999
        self.item_1    = data[0xB]
        self.rare_1    = data[0xC]
        self.item_2    = data[0xD]
        self.rare_2    = data[0xE]
    
    def pack(self):
        bitfield = sum([
            int(self.is_spiked) << 0,
            int(self.is_flying) << 2,
            self.fire_damage  <<  3,
            self.burn_chance  <<  8,
            self.dizzy_chance << 10,
            self.stat_chance  << 12,
            self.insta_chance << 14,
            int(self.unk0) << 16,
            int(self.unk1) << 17,
        ])

        return struct.pack(
            '<2HIxBh3HI6H2x',
            self.name,
            self.script,
            self.obj_id,
            self.level,
            self.HP,
            self.POW,
            self.DEF,
            self.SPEED,
            bitfield,
            self.EXP,
            self.coins,
            self.item_1,
            self.rare_1,
            self.item_2,
            self.rare_2,
        )