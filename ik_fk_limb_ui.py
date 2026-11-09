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
        self.resize(800, 600)

        ####################################################################
        # Set up UI
        ####################################################################
        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        l_arm_btn = QPushButton("L arm IK/FK")
        l_arm_btn.clicked.connect(lambda: self.apply("l_arm"))
        r_arm_btn = QPushButton("r arm IK/FK")
        r_arm_btn.clicked.connect(lambda: self.apply("r_arm"))
        l_leg_btn = QPushButton("L leg IK/FK")
        l_leg_btn.clicked.connect(lambda: self.apply("l_leg"))
        r_leg_btn = QPushButton("r leg IK/FK")
        r_leg_btn.clicked.connect(lambda: self.apply("r_leg"))
        layout.addWidget(l_arm_btn)
        layout.addWidget(r_arm_btn)
        layout.addWidget(l_leg_btn)
        layout.addWidget(r_leg_btn)

    def apply(self, limb):
        cmds.undoInfo(openChunk=True, chunkName="Ik FK Limb")

        try:
            ik_fk_util = limb_util.IKFKUtil()

            joints = cmds.ls(sl=True, type="joint")

            # Only build IK/FK for human limb
            if len(joints) != 3:
                cmds.warning("The number of selected joints must be 3")
                return

            ik_fk_util.build(limb, joints)
        finally:
            cmds.undoInfo(closeChunk=True)


MENU_NAME = "markingMenu"

class MarkingMenu():
    def __init__(self) -> None:
        self._removeOld()
        self._build()

    def _buildMarkingMenu(self, menu, parent):
        # Radial positioned
        cmds.menuItem(p=menu, l="Ik Fk Switch SameOrient", rp='N', command=self.ikFkSwitch_sameOrient)
        cmds.menuItem(p=menu, l="Ik Fk Switch IkWorld", rp='S', command=self.ikFkSwitch_ikWorld)
        print("update menu\n")


    def _removeOld(self):
        if cmds.popupMenu(MENU_NAME, ex=True):
            cmds.deleteUI(MENU_NAME)

    def _build(self):
        menu = cmds.popupMenu(MENU_NAME, mm=True, b=2, aob=True, ctl=True, alt=True, sh=False, p="viewPanes", pmo=True, pmc=self._buildMarkingMenu)

    # Seamless ik fk switch
    def ikFkSwitch_sameOrient(self, *args):
        ikfkutil = limb_util.IKFKUtil()
        ikfkutil.ikFkSwitch_sameOrient()

    def ikFkSwitch_ikWorld(self, *args):
        ikfkutil = limb_util.IKFKUtil()
        ikfkutil.ikFkSwitch_ikWorld()


window = None

def show():
    global window

    if window is not None:
        window.close()

    main_window_ptr = omui.MQtUtil.mainWindow()
    main_window = wrapInstance(int(main_window_ptr), QW.QWidget)

    window = LimbIKFKUI(main_window)

    marking_menu = MarkingMenu()

    window.show()