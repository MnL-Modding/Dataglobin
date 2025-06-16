import os
import io
import sys
import struct
from random import choice
from PySide6 import QtCore, QtGui, QtMultimedia, QtWidgets
import ndspy.rom
import ndspy.code
from mnllib.bis import LanguageTable, TextTable, BIS_ENCODING

# BIS_ENCODING = "shift_jis"

from dataglobin.constants import *
from dataglobin.data_classes import EnemyData
from dataglobin.tab_enemy_data import EnemyDataTab

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.setWindowTitle(APP_DISPLAY_NAME)
        self.setWindowIcon(QtGui.QIcon(str(FILES_DIR / 'dataglobin.ico')))

        self.success_sfx = QtMultimedia.QSoundEffect(self)
        self.success_sfx.setSource(QtCore.QUrl.fromLocalFile(FILES_DIR / "dataglobin_success.wav"))
        self.success_sfx.setVolume(0.3)

        menu_bar = self.menuBar()
        menu_bar_file = menu_bar.addMenu("&File")
        menu_bar_file.addAction(
            "&Import",
            QtGui.QKeySequence.StandardKey.Open,
            self.init_ui,
        )
        menu_bar_file.addAction(
            "&Export",
            QtGui.QKeySequence.StandardKey.Save,
            self.export_rom,
        )
        menu_bar_file.addSeparator() # -----------------------------------------
        menu_bar_file.addAction(
            "&Quit",
            QtGui.QKeySequence.StandardKey.Quit,
            QtWidgets.QApplication.quit,
        )

        self.program_is_already_open = False
        self.init_ui()
    
    def init_ui(self):
        QtWidgets.QMessageBox.information(
            self,
            "Choose a ROM",
            f"Please choose a North American or European Bowser's Inside Story ROM to open.",
        )

        self.chose_rom = False
        self.import_rom()
        while self.chose_rom == False and not self.program_is_already_open:
            self.import_rom()

        main = QtWidgets.QTabWidget()

        self.enemy_data_tab = EnemyDataTab(self.monster_data, self.monster_names, self.overlay_BObjMon_offsets, self.overlay_BObj, self.BObjMon_file)

        main.addTab(self.enemy_data_tab, "Enemy Data")
        
        self.setCentralWidget(main)

    def import_rom(self):
        path, _selected_filter = QtWidgets.QFileDialog.getOpenFileName(
            parent=self,
            caption="Open ROM",
            filter=NDS_ROM_FILENAME_FILTER,
        )
        if path == '':
            if not self.program_is_already_open:
                sys.exit(2)
            else:
                return
        
        self.current_path = path

        self.rom = ndspy.rom.NintendoDSRom.fromFile(path)

        if self.rom.name != b"MARIO&LUIGI3":
            QtWidgets.QMessageBox.warning(
                self,
                "Invalid ROM",
                f"The chosen ROM is not a valid Bowser's Inside Story ROM.",
            )
            return

        if self.rom.idCode[3] == 69 or self.rom.idCode[3] == 80:                  # US-base
            self.chose_rom = True
            self.overlays = self.rom.loadArm9Overlays()
            self.overlay_enemy_stats = self.overlays[11]
            self.overlay_enemy_stats_offset = 0xE074
            self.overlay_BObj = [self.rom.loadArm9Overlays([14])[14].data, self.rom.loadArm9Overlays([13])[13].data]
            self.overlay_BObjMon_offsets = (0x9C18, 0x84D8, 0x6610) # filedata, sprite groups, palette groups
            self.rom_base = 1
        else:                                                                     # JP-base                                   
            QtWidgets.QMessageBox.warning(
                self,
                "Invalid ROM",
                f"The chosen ROM is not from a valid region.\n\nOnly a North American or European Bowser's Inside Story ROM will work.",
            )
            return
            # self.overlay_enemy_stats = rom.loadArm9Overlays([126])[126].data
            # self.overlay_enemy_stats_offset =
            self.rom_base = 0
        self.program_is_already_open = True
        
        self.BObjMon_file = self.rom.getFileByName('BObjMon/BObjMon.dat')
        mfset_MonN = self.rom.getFileByName('BData/mfset_MonN.dat')

        self.rom_to_pack = self.rom
        
        # -------------------------------------------------------------------------------
        # read monster data
        
        self.monster_names = [[], [], [], [], [], []]
        monster_names = LanguageTable.from_bytes(mfset_MonN, False)
        for i in range(6):
            if monster_names.text_tables[i + 1]:
                for string in monster_names.text_tables[i + 1].entries:
                    index = string.index(0xFF)
                    self.monster_names[i].append(string[:index].decode(BIS_ENCODING, "ignore"))

        self.monster_data = []
        monster_data = io.BytesIO(self.overlay_enemy_stats.data)
        monster_data.seek(self.overlay_enemy_stats_offset)
        length_test = monster_data.read()
        for i in range(len(length_test) // 0x24):
            monster_data.seek(self.overlay_enemy_stats_offset + (i * 0x24))
            monster_data_in = monster_data.read(0x24)
            self.monster_data.append(EnemyData(monster_data_in))

    def export_rom(self):
        path, selected_filter = QtWidgets.QFileDialog.getSaveFileName(
            parent=self,
            caption="Save ROM",
            dir=self.current_path,
            filter=NDS_ROM_FILENAME_FILTER,
        )

        if path == '':
            return
        self.current_path = path
        
        # -------------------------------------------------------------------------------
        # write monster data

        monster_data = io.BytesIO(self.overlay_enemy_stats.data)
        monster_data.seek(self.overlay_enemy_stats_offset)
        length_test = monster_data.read()
        for i in range(len(length_test) // 0x24):
            monster_data.seek(self.overlay_enemy_stats_offset + (i * 0x24))
            monster_data.write(self.enemy_data_tab.monster_data[i].pack())

        monster_data.seek(0)
        self.overlay_enemy_stats.data = monster_data.read()

        current_lang_all = [b'']
        for i in range(6):
            current_lang = [name.encode(BIS_ENCODING) + b'\xFF\x0A\x00' for name in self.enemy_data_tab.monster_names[i]]

            text_table_packed = TextTable(current_lang, False).to_bytes()
            if len(text_table_packed) % 4 != 0:
                text_table_packed += bytes(4 - (len(text_table_packed) % 4))
            current_lang_all.append(text_table_packed)

        current_lang_all.append(b'')
        
        mfset_MonN_packed = LanguageTable(current_lang_all, False).to_bytes()
        if len(mfset_MonN_packed) % 0x200 != 0:
            mfset_MonN_packed += bytes(0x200 - (len(mfset_MonN_packed) % 0x200))
        
        self.rom_to_pack.setFileByName('BData/mfset_MonN.dat', mfset_MonN_packed)

        # -------------------------------------------------------------------------------

        self.rom_to_pack.files[self.overlays[11].fileID] = self.overlay_enemy_stats.save(compress = True)
        self.rom_to_pack.arm9OverlayTable = ndspy.code.saveOverlayTable(self.overlays)
        self.rom_to_pack.saveToFile(path)

        self.success_sfx.play()
        QtWidgets.QMessageBox.about(
            self,
            "Export Successful",
            f"Successfully exported ROM to:\n\n{path}",
        )