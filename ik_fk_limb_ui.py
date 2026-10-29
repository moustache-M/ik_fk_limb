"""
Auto build FK/IK and switch between them By Zhou Pengfei.
Note: This script is only for human limb. 
      I haven't learned rig for other creatures yet.
      I will improve it for other creatures in the future
"""

import ik_fk_limb_util as limb_util
from importlib import reload
reload(limb_util)


import maya.cmds as cmds
from maya import OpenMayaUI as omui   # type: ignore
from shiboken6 import wrapInstance


import PySide6

from PySide6 import QtWidgets as QW
from PySide6.QtWidgets import (
    QWidget,
    QMainWindow,
    QVBoxLayout,
    QPushButton,
)



class LimbIKFKUI(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        ####################################################################
        # Set up UI
        ####################################################################
        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        l_arm_btn = QPushButton("L arm IK/FK")
        l_arm_btn.clicked.connect(self.apply("l_arm"))
        r_arm_btn = QPushButton("r arm IK/FK")
        l_arm_btn.clicked.connect(self.apply("r_arm"))
        l_leg_btn = QPushButton("L leg IK/FK")
        l_arm_btn.clicked.connect(self.apply("l_leg"))
        r_leg_btn = QPushButton("r leg IK/FK")
        l_arm_btn.clicked.connect(self.apply("r_leg"))
        layout.addWidget(l_arm_btn)
        layout.addWidget(r_arm_btn)
        layout.addWidget(l_leg_btn)
        layout.addWidget(r_leg_btn)

    def apply(self, limb):
        ik_fk_util = limb_util.IKFKUtil()

        joints = cmds.ls(sl=True, type="joint")

        # Only build IK/FK for human limb
        if len(joints) != 3:
            cmds.warning("The number of selected joints must be 3")

        ik_fk_util.build(limb, joints)

def show():
    global window
    window = None

    if window is not None:
        window.close()
        window = None

    if window is None:
        main_window_ptr = omui.MQtUtil.mainWindow()
        main_window = wrapInstance(int(main_window_ptr), QW.QWidget)

        window = LimbIKFKUI(QMainWindow)

    window.show()