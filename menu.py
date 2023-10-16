"""
Copyright (C) 2023 Abraham George Smith

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

from PyQt6.QtWidgets import (
    QWidget, QLabel 
)
from PyQt6.QtGui import QAction, QIcon

from about import AboutWindow, LicenseWindow


def add_menu_bar(window):
    add_about_menu(window)
    
def add_about_menu(window):
    menu_bar = window.menuBar()
    about_menu = menu_bar.addMenu('About')

    def show_license_window():
        window.license_window = LicenseWindow()
        window.license_window.show()

    def show_about_window():
        window.about_window = AboutWindow()
        window.about_window.show()

    license_btn = QAction(QIcon('missing.png'), 'License', window)
    license_btn.triggered.connect(show_license_window)

    about_menu.addAction(license_btn)
    about_btn = QAction(QIcon('missing.png'),
                                  'SeminalRootAngleExtractor', window)
    about_btn.triggered.connect(show_about_window)
    about_menu.addAction(about_btn)


