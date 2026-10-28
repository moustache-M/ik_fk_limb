import maya.cmds as cmds # type: ignore

class IKFKUtil():

    def shortName(self, name: str):
        return name.split("|")[-1]

    def clean_duplicate_suffix(self, name: str):
        """
        Maya duplicate by adding a number, like l_humerus1
        This function remove the number at the end
        """
        while name and name[-1].isdigit():
            name = name[:-1]

        return name

    def apply(self, joints: list[str]):
        pass


    def switchIkFK(self, switch: str, joints: list[str], fk_joints: list[str], ik_joints: list[str]):

        # Add switch attribute, 0 to disable IK, 1 to enable IK
        cmds.addAttr(switch, longName="ikFkSwitch", defaultValue=0, minValue=0, maxValue=1, keyable=True)

        reverse = cmds.createNode("reverse", name=switch+"_reverse")

        cmds.connectAttr(f"{switch}.ikFKSwitch", f"{reverse}.inputX", force=True)

        for fk_joint, ik_joint, joint in zip(fk_joints, ik_joints, joints):
            constraint = cmds.parentConstraint(fk_joint, ik_joint, joint, mo=False)[0]
            weight_aliases = cmds.parentConstraint(constraint, query=True, weightAliasList=True)

            for alias in weight_aliases:
                if "fk" in alias:
                    cmds.connectAttr(f"{reverse}.outputX", f"{constraint}.{alias}", force=True)
                else:
                    cmds.connectAttr(f"{switch}.ikFKSwitch", f"{constraint}.{alias}", force=True)


    def SwitchCtrl(self, body_part: str, side: str, pos: tuple[float, float, float]) -> str:
        name = body_part + "_" + side + "_ik_fk_switch"
        switch_ctrl = createController.twoArrow(name=name)

        cmds.move(switch_ctrl, *pos, worldSpace=True)
        cmds.makeIdentity(switch_ctrl, t=True)

        return switch_ctrl

    def buildFKLimb(self, fk_joints: list[str]):
        fk_ctrls = []
        for i in range(len(fk_joints)):
            # Add FK ctrl
            fk_ctrl = createController.circle(name=fk_joints[i]+"_ctrl", r=1.0, n=(0,1,0))
            fk_ctrls.append(fk_ctrl)

            # Parent fk ctrls together
            if i > 0:
                cmds.parent(fk_ctrls[i], fk_ctrls[i-1])



        # Place using offset parent matrix (Keep localMatrix = identityMatrix)
        # Formula: self_worldMatrix = self_localMatrix * self_offsetParentMatrix * parent_worldMaxtrix
        for i in range(len(fk_joints)):

            if i > 0:
                # self_offsetParentMatrix = self_worldMatrix * inverse( parent_worldMatrix )
                mult = cmds.createNode('multMatrix')
                cmds.connectAttr('{}.worldMatrix[0]'.format(fk_joints[i]), '{}.matrixIn[0]'.format(mult))
                cmds.connectAttr('{}.worldInverseMatrix[0]'.format(fk_ctrls[i-1]), '{}.matrixIn[1]'.format(mult))
                cmds.connectAttr('{}.matrixSum'.format(mult), '{}.offsetParentMatrix'.format(fk_ctrls[i]))

                cmds.disconnectAttr('{}.matrixSum'.format(mult), '{}.offsetParentMatrix'.format(fk_ctrls[i]))
                cmds.delete(mult)
            else:
                # self_offsetParentMatrix = self_worldMatrix
                cmds.connectAttr('{}.worldMatrix[0]'.format(fk_joints[i]), '{}.offsetParentMatrix'.format(fk_ctrls[i]))
                cmds.disconnectAttr('{}.worldMatrix[0]'.format(fk_joints[i]), '{}.offsetParentMatrix'.format(fk_ctrls[i]))


    def buildIkLimb(self, body_part: str, ik_joints: list[str]):

        ikHandle = body_part + "_ikHandle"
        pv = body_part + "_pv_ctrl"

        # Add IK handle
        cmds.ikHandle(name= ikHandle, sol="ikRPSolver", sj=ik_joints[0], ee=ik_joints[-1])

        # Add IK ctrl
        ik_ctrl = createController.fourArrow(name=body_part+"_"+side+"_ik_ctrl")
        cmds.matchTransform(ik_ctrl, ik_joints[-1], position=True)
        self.bake_trs_offsetParentMatrix(ik_ctrl)

        cmds.parent(ikHandle, ik_ctrl)

        # Add PV ctrl
        self.addPV(ik_joints, pv)

    def addPV(self, ik_joints: list[str], name: str) -> str:

        return name

    # origin: https://github.com/vertexTheory/ik_fk_limb/blob/master/video3_ik_fk_limb.py#L123
    def bake_trs_offsetParentMatrix(self, transform: str):
        '''
        Bake TRS value into offsetParentMatrix

        '''

        # duplicate transform to place with offsetParentMatrix
        temp = cmds.duplicate(transform, po=True)[0]

        parent = None

        try:
            parent = cmds.listRelatives(transform, p=True)[0]
        except:
            pass

        # self_offsetParentMatrix = self_worldMatrix * inverse( parent_worldMatrix )
        if parent:
            mult = cmds.createNode('multMatrix')
            cmds.connectAttr('{}.worldMatrix[0]'.format(temp), '{}.matrixIn[0]'.format(mult))
            cmds.connectAttr('{}.worldInverseMatrix[0]'.format(parent), '{}.matrixIn[1]'.format(mult))
            cmds.connectAttr('{}.matrixSum'.format(mult), '{}.offsetParentMatrix'.format(transform))
        else:
            cmds.connectAttr('{}.worldMatrix'.format(temp), '{}.offsetParentMatrix'.format(transform))
            cmds.disconnectAttr('{}.worldMatrix'.format(temp), '{}.offsetParentMatrix'.format(transform))

        # delete temp transform
        cmds.delete(temp)


    # origin: https://github.com/vinL1234/auto-limb-tool/blob/main/auto_limb_tool/core.py#L92
    def duplicate_joints(self, root_joint, suffix):
        '''
        Duplicate the full hierachy and rename it from children to root.
        '''
        dup_root = cmds.duplicate(root_joint, renameChildren=True)[0]

        dup_root = (
                    cmds.ls(dup_root, long=True, type="joint") 
                    or [dup_root]
                    )[0]

        dup_joints = cmds.listRelatives(dup_root, type="joint", allDescendents=True, fullPath=True) or []

        dup_joints.append(dup_root)

        # Important:
        # Rename deepest children first
        # If rename the root first, all child full path change and 

        dup_joints







class createController():

    @staticmethod
    def circle(name: str, r: float, n: tuple[float, float, float]) -> str:
        cmds.circle(name=name, radius=r, normal=n)
        return name

    @staticmethod
    def fourArrow(name: str) -> str:
        cmds.curve(name=name, d=1, p=ctrlShapes.four_arrow)
        return name

    @staticmethod
    def twoArrow(name: str) -> str:
        cmds.curve(name=name, d=1, p=ctrlShapes.two_arrow)
        return name

class ctrlShapes():

    four_arrow = [
        ( 0.0, 0.0, -25.0 ),
        ( -10.0, 0.0, -15.0 ),
        ( -5.0, 0.0, -15.0 ),
        ( -5.0, 0.0, -5.0 ),
        ( -15.0, 0.0, -5.0 ),
        ( -15.0, 0.0, -10.0 ),
        ( -25.0, 0.0, 0.0 ),
        ( -15.0, 0.0, 10.0 ),
        ( -15.0, 0.0, 5.0 ),
        ( -5.0, 0.0, 5.0 ),
        ( -5.0, 0.0, 15.0 ),
        ( -10.0, 0.0, 15.0 ),
        ( 0.0, 0.0, 25.0 ),
        ( 10.0, 0.0, 15.0 ),
        ( 5.0, 0.0, 15.0 ),
        ( 5.0, 0.0, 5.0 ),
        ( 15.0, 0.0, 5.0 ),
        ( 15.0, 0.0, 10.0 ),
        ( 25.0, 0.0, 0.0 ),
        ( 15.0, 0.0, -10.0 ),
        ( 15.0, 0.0, -5.0 ),
        ( 5.0, 0.0, -5.0 ),
        ( 5.0, 0.0, -15.0 ),
        ( 10.0, 0.0, -15.0 ),
        ( 0.0, 0.0, -25.0 )
    ]

    two_arrow = [
        ( -10.0, 0.0, -15.0 ),
        ( -20.0, 0.0, 0.0 ),
        ( -10.0, 0.0, 15.0 ),
        ( -10.0, 0.0, 5.0 ),
        ( 10.0, 0.0, 5.0 ),
        ( 10.0, 0.0, 15.0 ),
        ( 20.0, 0.0, 0.0 ),
        ( 10.0, 0.0, -15.0 ),
        ( 10.0, 0.0, -5.0 ),
        ( -10.0, 0.0, -5.0 ),
        ( -10.0, 0.0, -15.0 )
    ]


