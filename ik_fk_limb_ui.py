import maya.cmds as cmds
import PySide6

from PySide6 import QtWidgets as QW
from PySide6.QtWidgets import (
    QWidget,
    QMainWindow,
    QVBoxLayout,
    QPushButton,
)


class UI(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        ####################################################################
        # Set up UI
        ####################################################################
        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        apply_btn = QPushButton("Apply")
        layout.addWidget(apply_btn)

    def apply(self):
        joints = cmds.ls(sl=True)









