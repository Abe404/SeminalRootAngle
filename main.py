"""
Copyright (C) 2022 Abraham George Smith
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import os
import sys
from PyQt5 import QtWidgets 
from PyQt5 import QtCore
from PyQt5 import QtGui


class MainWindow(QtWidgets.QMainWindow):

    def create_ui(self):
        pass

    def __init__(self):
        super().__init__()
        self.setStyleSheet("""
            QPushButton{font-size: 14pt;}
            QComboBox{font-size: 11pt;}
        """)
        self.create_ui()


app = QtWidgets.QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec_())
