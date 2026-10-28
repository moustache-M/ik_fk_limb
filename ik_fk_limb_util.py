import maya.cmds as cmds

class IKFKUtil():
    def __init__(self):
        pass

    def apply(self, joints: list[str]):
        pass


    def addIkFk(self, joints: list[str]):

        # Build Fk joints
        for joint in joints:
            cmds.joint(name=joint+"_fk")
            cmds.matchTransform(joint+"_fk", joint)

        # Clear selection
        cmds.select(clear=True)

        # Build Ik joints
        for joint in joints:
            cmds.joint(name=joint+"_fk")
            cmds.matchTransform(joint+"_fk", joint)

        # Add constraints
        for joint in joints:
            cmds.parentConstraint(joint+"_fk", joint+"_ik", joint, w=True, mo=True)

    def switchIkFK(self, switch: str, fk_joints: list[str], ik_joints: list[str]):

        # Add switch attribute
        cmds.addAttr(switch, longName="ikFkSwitch", defaultValue=0, minValue=0, maxValue=1, keyable=True)

        # Add



        pass


    def addSwitchCtrl(self, body_part: str, side: str, pos: tuple[float, float, float]) -> str:
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



    def buildIkLimb(self, body_part: str, side: str, ik_joints: list[str]):

        ikHandle = body_part + "_" + side + "_ikHandle"

        # Add IK handle
        cmds.ikHandle(name= ikHandle, sol="ikRPSolver", sj=ik_joints[0], ee=ik_joints[-1])

        # Add IK ctrl
        ik_ctrl = createController.fourArrow(name=body_part+"_"+side+"_ik_ctrl")
        cmds.matchTransform(ik_ctrl, ik_joints[-1], position=True)

        cmds.parent(ikHandle, ik_ctrl)

    def addIk(self, ik_joints: list[str], name: str) -> str:


        return name



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


