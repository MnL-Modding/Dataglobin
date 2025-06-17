from PySide6 import QtCore, QtGui, QtWidgets
from functools import partial

from dataglobin.image import create_sprite, image_crop
from dataglobin.constants import *

class EnemyDataTab(QtWidgets.QWidget):
    def __init__(self, monster_data, monster_names, overlay_BObjMon_offsets, overlay_BObj, BObjMon_file):
        super().__init__()

        self.monster_data = monster_data
        self.monster_names = monster_names
        self.overlay_BObjMon_offsets = overlay_BObjMon_offsets
        self.overlay_BObj = overlay_BObj
        self.BObjMon_file = BObjMon_file

        main_layout = QtWidgets.QVBoxLayout(self)

        self.name_edit_widgets = []

        # ======================================================================================================================

        label = QtWidgets.QLabel("Ene&my")
        main_layout.addWidget(label)

        self.monster_choose_box = QtWidgets.QComboBox()
        label.setBuddy(self.monster_choose_box)
        for i, monster in enumerate(self.monster_data):
            self.monster_choose_box.addItem(self.draw_monster_sprite(i, True), self.monster_names[1][monster.name])
        self.monster_choose_box.currentIndexChanged.connect(self.update_all_monster_stats)
        main_layout.addWidget(self.monster_choose_box)

        # monster properties

        monster_properties = QtWidgets.QWidget()
        monster_properties_layout = QtWidgets.QGridLayout(monster_properties)
        main_layout.addWidget(monster_properties)

        self.all_stats = []

        # monster properties - appearance

        monster_properties_appearance = QtWidgets.QWidget()
        monster_properties_appearance_layout = QtWidgets.QGridLayout(monster_properties_appearance)
        monster_properties_appearance_layout.setContentsMargins(0, 0, 0, 0)
        monster_properties_layout.addWidget(monster_properties_appearance, 0, 0, 5, 1)

        self.monster_image = QtWidgets.QLabel()
        self.monster_image.setFixedSize(200, 200)
        self.monster_image.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        monster_properties_appearance_layout.addWidget(self.monster_image, 0, 1, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)
        
        label = QtWidgets.QLabel("&Name")
        box = QtWidgets.QComboBox()
        box.addItems(self.monster_names[1])
        box.currentIndexChanged.connect(self.change_monster_name)
        monster_properties_appearance_layout.addWidget(box, 2, 1)
        self.all_stats.append(box)
        label.setBuddy(box)
        monster_properties_appearance_layout.addWidget(label, 1, 1)
        
        label = QtWidgets.QLabel("Scrip&t ID")
        box = QtWidgets.QLineEdit()
        box.textEdited.connect(partial(self.change_monster_stat, len(self.all_stats)))
        box.setInputMask("HHHH")
        box.setText("0000")
        monster_properties_appearance_layout.addWidget(box, 4, 1)
        self.all_stats.append(box)
        label.setBuddy(box)
        monster_properties_appearance_layout.addWidget(label, 3, 1)
        
        label = QtWidgets.QLabel("&Obj ID")
        box = ObjectIDSpinBox()
        box.valueChanged.connect(self.change_monster_object)
        box.setMaximum(0x151 - 1)
        monster_properties_appearance_layout.addWidget(box, 6, 1)
        self.all_stats.append(box)
        label.setBuddy(box)
        monster_properties_appearance_layout.addWidget(label, 5, 1)

        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.VLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        monster_properties_layout.addWidget(line, 0, 1, 5, 1)

        # monster properties - stats

        monster_properties_stats = QtWidgets.QWidget()
        monster_properties_stats_layout = QtWidgets.QGridLayout(monster_properties_stats)
        monster_properties_stats_layout.setContentsMargins(0, 0, 0, 0)
        monster_properties_layout.addWidget(monster_properties_stats, 0, 2)
        for i in range(5):
            label = QtWidgets.QLabel(["&LV", "&HP", "&POW", "&DEF", "&SPEED"][i])
            box = QtWidgets.QSpinBox()
            box.valueChanged.connect(partial(self.change_monster_stat, len(self.all_stats)))
            box.setMaximum([99, 0x7FFF, 999, 999, 999][i])
            monster_properties_stats_layout.addWidget(box, 1, i)

            self.all_stats.append(box)
            label.setBuddy(box)
            monster_properties_stats_layout.addWidget(label, 0, i)

        # monster properties - properties

        monster_properties_properties = QtWidgets.QWidget()
        monster_properties_properties_layout = QtWidgets.QGridLayout(monster_properties_properties)
        monster_properties_properties_layout.setContentsMargins(0, 0, 0, 0)
        monster_properties_layout.addWidget(monster_properties_properties, 2, 2)

        box = QtWidgets.QCheckBox("Spi&ky")
        box.checkStateChanged.connect(partial(self.change_monster_stat, len(self.all_stats)))
        monster_properties_properties_layout.addWidget(box, 0, 0, 2, 1)
        self.all_stats.append(box)

        box = QtWidgets.QCheckBox("&Flying")
        box.checkStateChanged.connect(self.change_monster_flying)
        monster_properties_properties_layout.addWidget(box, 0, 1, 2, 1)
        self.all_stats.append(box)

        for i in range(5):
            label = QtWidgets.QLabel(["Fi&re Damage", "&Burn Chance", "Di&zzy Chance", "St&at Down Chance", "&Instant KO Chance"][i])
            x_coord, y_coord = [(2, 0), (0, 1), (1, 1), (2, 1), (2, 2)][i]
            box = QtWidgets.QComboBox()
            if i == 0:
                box.addItems(["Normal", "Critical", "Half", "Immune"])
            else:
                box.addItems(["Normal", "Double", "Half", "Immune"])
            box.currentIndexChanged.connect(partial(self.change_monster_stat, len(self.all_stats)))
            monster_properties_properties_layout.addWidget(box, (y_coord * 2) + 1, x_coord)

            self.all_stats.append(box)
            label.setBuddy(box)
            monster_properties_properties_layout.addWidget(label, y_coord * 2, x_coord)

        box = QtWidgets.QCheckBox("Unknown &1")
        box.checkStateChanged.connect(partial(self.change_monster_stat, len(self.all_stats)))
        monster_properties_properties_layout.addWidget(box, 4, 0, 2, 1)
        self.all_stats.append(box)

        box = QtWidgets.QCheckBox("Unknown &2")
        box.checkStateChanged.connect(partial(self.change_monster_stat, len(self.all_stats)))
        monster_properties_properties_layout.addWidget(box, 4, 1, 2, 1)
        self.all_stats.append(box)

        # monster properties - drops

        monster_properties_drops = QtWidgets.QWidget()
        monster_properties_drops_layout = QtWidgets.QGridLayout(monster_properties_drops)
        monster_properties_drops_layout.setContentsMargins(0, 0, 0, 0)
        monster_properties_layout.addWidget(monster_properties_drops, 4, 2)
        
        label = QtWidgets.QLabel("E&XP")
        box = QtWidgets.QSpinBox()
        box.valueChanged.connect(partial(self.change_monster_stat, len(self.all_stats)))
        box.setMaximum(9999)
        monster_properties_drops_layout.addWidget(box, 1, 0)
        self.all_stats.append(box)
        label.setBuddy(box)
        monster_properties_drops_layout.addWidget(label, 0, 0)
        
        label = QtWidgets.QLabel("&Coins")
        box = QtWidgets.QSpinBox()
        box.valueChanged.connect(partial(self.change_monster_stat, len(self.all_stats)))
        box.setMaximum(9999)
        monster_properties_drops_layout.addWidget(box, 3, 0)
        self.all_stats.append(box)
        label.setBuddy(box)
        monster_properties_drops_layout.addWidget(label, 2, 0)
        
        label = QtWidgets.QLabel("&Normal Item")
        box = QtWidgets.QLineEdit()
        box.textEdited.connect(partial(self.change_monster_stat, len(self.all_stats)))
        box.setMaxLength(4)
        box.setInputMask("HHHH")
        box.setText("0000")
        monster_properties_drops_layout.addWidget(box, 1, 1)
        self.all_stats.append(box)
        label.setBuddy(box)
        monster_properties_drops_layout.addWidget(label, 0, 1)
        
        label = QtWidgets.QLabel("&Normal Drop Rate")
        box = QtWidgets.QSpinBox()
        box.valueChanged.connect(partial(self.change_monster_stat, len(self.all_stats)))
        box.setMaximum(100)
        box.setSuffix("%")
        monster_properties_drops_layout.addWidget(box, 1, 2, 1, 2)
        self.all_stats.append(box)
        label.setBuddy(box)
        monster_properties_drops_layout.addWidget(label, 0, 2, 1, 2)
        
        label = QtWidgets.QLabel("&Rare Item")
        box = QtWidgets.QLineEdit()
        box.textEdited.connect(partial(self.change_monster_stat, len(self.all_stats)))
        box.setMaxLength(4)
        box.setInputMask("HHHH")
        box.setText("0000")
        monster_properties_drops_layout.addWidget(box, 3, 1)
        self.all_stats.append(box)
        label.setBuddy(box)
        monster_properties_drops_layout.addWidget(label, 2, 1)
        
        label = QtWidgets.QLabel("&Rare Drop Rate")
        label.setStyleSheet("QLabel { text-decoration: underline; }")
        box = QtWidgets.QSpinBox()
        box.valueChanged.connect(partial(self.change_monster_stat, len(self.all_stats)))
        box.setMaximum(100)
        box.setSuffix("%")
        monster_properties_drops_layout.addWidget(box, 3, 2, 1, 2)
        self.all_stats.append(box)
        label.setBuddy(box)
        monster_properties_drops_layout.addWidget(label, 2, 2, 1, 2)
        
        tooltip_string = "This is the percentage of the Normal Drop Rate that will result\nin you receiving the Rare Item instead of the Normal Item."
        label.setToolTip(tooltip_string)
        box.setToolTip(tooltip_string)

        # ======================================================================================================================

        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        main_layout.addWidget(line)

        # name list box

        text_files = QtWidgets.QTabWidget()
        main_layout.addWidget(text_files)

        name_customizer = QtWidgets.QWidget()
        name_customizer_layout = QtWidgets.QGridLayout(name_customizer)
        text_files.addTab(name_customizer, "Monster Names")

        self.valid_languages = []
        lang = 0
        for name_list in self.monster_names:
            if name_list:
                self.valid_languages.append(lang)
            lang += 1

        self.monster_name_box = QtWidgets.QListWidget()
        for i in range(len(self.monster_names[self.valid_languages[0]])):
            string_list = []
            for j in self.valid_languages:
                string_list.append(self.monster_names[j][i])
            self.monster_name_box.addItem(", ".join(string_list))
        self.monster_name_box.setCurrentRow(0)
        self.monster_name_box.currentRowChanged.connect(self.update_name_edit_fields)
        name_customizer_layout.addWidget(self.monster_name_box, 0, 0, 12, 1)

        for i in range(6):
            language_name = QtWidgets.QLabel(LANGUAGE_NAMES[i])
            name_edit_field = QtWidgets.QLineEdit()

            lang_is_valid = i in self.valid_languages
            language_name.setEnabled(lang_is_valid)
            name_edit_field.setEnabled(lang_is_valid)
            if not lang_is_valid:
                name_edit_field.setText("(None)")

            name_edit_field.textEdited.connect(partial(self.update_monster_names, i))
            self.name_edit_widgets.append(name_edit_field)

            name_customizer_layout.addWidget(language_name, i * 2, 1)
            name_customizer_layout.addWidget(name_edit_field, i * 2 + 1, 1)
        
        self.update_name_edit_fields()
        self.update_all_monster_stats(self.monster_choose_box.currentIndex())
    
    def update_name_edit_fields(self):
        for lang in self.valid_languages:
            self.name_edit_widgets[lang].setText(self.monster_names[lang][self.monster_name_box.currentRow()])
    
    def update_monster_names(self, lang, text):
        self.monster_names[lang][self.monster_name_box.currentRow()] = text

        string_list = []
        for j in self.valid_languages:
            string_list.append(self.monster_names[j][self.monster_name_box.currentRow()])
            
        self.monster_name_box.currentItem().setText(", ".join(string_list))

        for i in range(self.monster_choose_box.count()):
            self.monster_choose_box.setItemText(i, self.monster_names[1][self.monster_data[i].name])
        for i in range(self.all_stats[0].count()):
            self.all_stats[0].setItemText(i, self.monster_names[1][i])
    
    def update_all_monster_stats(self, index):
        self.monster_image.setPixmap(self.draw_monster_sprite(index))
        
        for thingy in self.all_stats:
            thingy.blockSignals(True)

        self.all_stats[ 0].setCurrentIndex(self.monster_data[index].name)
        self.all_stats[ 1].setText(format(self.monster_data[index].script, 'x'))
        if self.monster_data[index].obj_id & 0xFFFF0000 != 0:
            self.all_stats[ 2].setValue(self.monster_data[index].obj_id & 0xFFFF)
        elif self.monster_data[index].obj_id == 0x00000000:
            self.all_stats[ 2].setValue(-1)
        elif self.monster_data[index].obj_id == 0x0000FFFF:
            self.all_stats[ 2].setValue(-2)

        self.all_stats[ 3].setValue(self.monster_data[index].level)
        self.all_stats[ 4].setValue(self.monster_data[index].HP)
        self.all_stats[ 5].setValue(self.monster_data[index].POW)
        self.all_stats[ 6].setValue(self.monster_data[index].DEF)
        self.all_stats[ 7].setValue(self.monster_data[index].SPEED)

        self.all_stats[ 8].setChecked(self.monster_data[index].is_spiked)
        self.all_stats[ 9].setChecked(self.monster_data[index].is_flying)

        self.all_stats[10].setCurrentIndex(self.monster_data[index].fire_damage)
        self.all_stats[11].setCurrentIndex(self.monster_data[index].burn_chance)
        self.all_stats[12].setCurrentIndex(self.monster_data[index].dizzy_chance)
        self.all_stats[13].setCurrentIndex(self.monster_data[index].stat_chance)
        self.all_stats[14].setCurrentIndex(self.monster_data[index].insta_chance)

        self.all_stats[15].setChecked(self.monster_data[index].unk0)
        self.all_stats[16].setChecked(self.monster_data[index].unk1)

        self.all_stats[17].setValue(self.monster_data[index].EXP)
        self.all_stats[18].setValue(self.monster_data[index].coins)
        self.all_stats[19].setText(format(self.monster_data[index].item_1, 'x'))
        self.all_stats[20].setValue(self.monster_data[index].rare_1)
        self.all_stats[21].setText(format(self.monster_data[index].item_2, 'x'))
        self.all_stats[22].setValue(self.monster_data[index].rare_2)

        for thingy in self.all_stats:
            thingy.blockSignals(False)
    
    def change_monster_name(self, index):
        monster_index = self.monster_choose_box.currentIndex()
        self.monster_data[monster_index].name = index
        self.monster_choose_box.setItemText(monster_index, self.monster_names[1][index])
    
    def change_monster_object(self, index):
        monster_index = self.monster_choose_box.currentIndex()
        if index == -2:
            self.monster_data[monster_index].obj_id = 0x0000FFFF
        elif index == -1:
            self.monster_data[monster_index].obj_id = 0x00000000
        else:
            self.monster_data[monster_index].obj_id = index + 0xC1000000
        self.monster_image.setPixmap(self.draw_monster_sprite(monster_index))
        self.monster_choose_box.setItemIcon(monster_index, self.draw_monster_sprite(monster_index, True))
    
    def change_monster_flying(self, value):
        monster_index = self.monster_choose_box.currentIndex()
        self.monster_data[monster_index].is_flying = value == QtCore.Qt.CheckState.Checked
        self.monster_image.setPixmap(self.draw_monster_sprite(monster_index))
    
    def change_monster_stat(self, stat, value):
        index = self.monster_choose_box.currentIndex()

        match stat:
        #   case  0: self.monster_data[index].name; taken care of elsewhere
            case  1: self.monster_data[index].script = int(value, 16)
        #   case  2: self.monster_data[index].obj_id; taken care of elsewhere

            case  3: self.monster_data[index].level = value
            case  4: self.monster_data[index].HP = value
            case  5: self.monster_data[index].POW = value
            case  6: self.monster_data[index].DEF = value
            case  7: self.monster_data[index].SPEED = value

            case  8: self.monster_data[index].is_spiked = value == QtCore.Qt.CheckState.Checked
        #   case  9: self.monster_data[index].is_flying; taken care of elsewhere

            case 10: self.monster_data[index].fire_damage = value
            case 11: self.monster_data[index].burn_chance = value
            case 12: self.monster_data[index].dizzy_chance = value
            case 13: self.monster_data[index].stat_chance = value
            case 14: self.monster_data[index].insta_chance = value

            case 15: self.monster_data[index].unk0 = value == QtCore.Qt.CheckState.Checked
            case 16: self.monster_data[index].unk1 = value == QtCore.Qt.CheckState.Checked

            case 17: self.monster_data[index].EXP = value
            case 18: self.monster_data[index].coins = value
            case 19: self.monster_data[index].item_1 = int(value, 16)
            case 20: self.monster_data[index].rare_1 = value
            case 21: self.monster_data[index].item_2 = int(value, 16)
            case 22: self.monster_data[index].rare_2 = value
    
    def draw_monster_sprite(self, index, thumbnail = False):
        if self.monster_data[index].obj_id & 0xFFFF0000 != 0:
            tex, shadow_type = create_sprite(
                self.overlay_BObjMon_offsets,
                self.overlay_BObj,
                self.BObjMon_file,
                self.monster_data[index].obj_id & 0xFFFF, 0, 1)
            
            if thumbnail:
                tex = image_crop(tex)
                return tex

            base = create_sprite(
                self.overlay_BObjMon_offsets,
                self.overlay_BObj,
                self.BObjMon_file,
                0, shadow_type, 0)

            if self.monster_data[index].is_flying:
                y_offset = 32
            else:
                y_offset = 0

            tex1 = tex.copy()
            painter = QtGui.QPainter(tex)
            painter.setOpacity(0.5)
            painter.drawPixmap(0, y_offset, base)
            painter.setOpacity(1.0)
            painter.drawPixmap(0, 0, tex1)

            painter.end()
            tex = image_crop(tex)
        else:
            tex = QtGui.QPixmap(16, 16)
            tex.fill(QtCore.Qt.transparent)
        return tex

class ObjectIDSpinBox(QtWidgets.QSpinBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.special_values = {
            -1: "Null (0)",
            -2: "Null (-1)",
        }
        self.setMinimum(-2)

    def textFromValue(self, value):
        if value in self.special_values:
            return self.special_values[value]
        return super().textFromValue(value)

    def valueFromText(self, text):
        for value, special_text in self.special_values.items():
            if text == special_text:
                return value
        return super().valueFromText(text)
