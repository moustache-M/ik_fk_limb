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

    def build(self, limb, joints: list[str]):

        # Create fk and ik joints chain
        fk_joints = self.duplicate_joints(joints, "_fk")
        ik_joints = self.duplicate_joints(joints, "_ik")

        fk_ctrls = self.buildFKLimb(limb, fk_joints)
        ik_ctrls = self.buildIKLimb(limb, ik_joints)

        jnt_pos = cmds.xform(joints[-1], query=True, t=True, ws=True)
        switch_pos = (jnt_pos[0], jnt_pos[1], jnt_pos[2]-5)

        swich_ctrl = self.createSwitchCtrl(limb, switch_pos)

        self.switchIkFK(swich_ctrl, joints, fk_joints, ik_joints, fk_ctrls, ik_ctrls)

        print("Build done.\n")


    def switchIkFK(self, switch: str, joints: list[str], fk_joints: list[str], ik_joints: list[str], fk_ctrls: list[str], ik_ctrls: list[str]):

        # Add switch attribute, 0 to disable IK, 1 to enable IK
        cmds.addAttr(switch, longName="ikFkSwitch", defaultValue=0, minValue=0, maxValue=1, keyable=True)

        reverse = cmds.createNode("reverse", name=switch+"_reverse")

        cmds.connectAttr(f"{switch}.ikFkSwitch", f"{reverse}.inputX", force=True)

        for fk_joint, ik_joint, joint in zip(fk_joints, ik_joints, joints):
            constraint = cmds.parentConstraint(fk_joint, ik_joint, joint, mo=False)[0]
            weight_aliases = cmds.parentConstraint(constraint, query=True, weightAliasList=True)

            for alias in weight_aliases:
                if "fk" in alias:
                    cmds.connectAttr(f"{reverse}.outputX", f"{constraint}.{alias}", force=True)
                else:
                    cmds.connectAttr(f"{switch}.ikFkSwitch", f"{constraint}.{alias}", force=True)
        
        # Switch the visibility of fk and ik ctrl
        for fk_ctrl in fk_ctrls:
            cmds.connectAttr(f"{reverse}.outputX", f"{fk_ctrl}.visibility", force=True)
        for ik_ctrl in ik_ctrls:
            cmds.connectAttr(f"{switch}.ikFkSwitch", f"{ik_ctrl}.visibility", force=True)


    def createSwitchCtrl(self, limb: str, pos: tuple[float, float, float]) -> str:
        name = limb + "_ik_fk_switch"
        switch_ctrl = createController.twoArrow(name=name)

        cmds.move(pos[0], pos[1], pos[2], switch_ctrl, worldSpace=True)
        self.bake_trs_offsetParentMatrix(switch_ctrl)

        return switch_ctrl

    def buildFKLimb(self, limb: str, fk_joints: list[str]) -> list[str]:
        fk_ctrls = []
        for i in range(len(fk_joints)):
            # Add FK ctrl
            fk_ctrl = createController.circle(name=fk_joints[i]+"_ctrl", r=3.0, n=(0,1,0))
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

        for fk_ctrl, fk_joint in zip(fk_ctrls, fk_joints):
            cmds.parentConstraint(fk_ctrl, fk_joint, mo=False)


        return fk_ctrls

    def buildIKLimb(self, limb: str, ik_joints: list[str]) -> list[str]:

        ikHandle = limb + "_ikHandle"
        pv = limb + "_pv_ctrl"


        # Add IK handle
        cmds.ikHandle(name=ikHandle, sol="ikRPsolver", sj=ik_joints[0], ee=ik_joints[-1])

        # Add IK ctrl
        ik_ctrl = createController.fourArrow(name=limb+"_ik_ctrl")
        cmds.matchTransform(ik_ctrl, ik_joints[-1], position=True, rotation=True)
        self.bake_trs_offsetParentMatrix(ik_ctrl)

        cmds.parent(ikHandle, ik_ctrl)

        # Add PV ctrl
        self.addPV(limb+"_pv_ctrl", ikHandle, ik_joints)

        return [ik_ctrl, pv]

    def addPV(self, name: str, ikHandle: str, ik_joints: list[str]) -> str:
        # Get joints' position
        start_jnt = cmds.xform( ik_joints[0], query=True, ws=True, rp=True )
        mid_jnt = cmds.xform( ik_joints[1], query=True, ws=True, rp=True )
        end_jnt = cmds.xform( ik_joints[2], query=True, ws=True, rp=True )

        pv_ctrl = createController.pyramid(name)

        # Calculate the position of PV
        # bend vector = middle_jnt - mid(end_jnt, start_jnt) 
        # pv_pos = middle_jnt + scale * bend vector
        mid_point = [(a+b)/2 for a,b in zip(end_jnt, start_jnt)]
        bend_vector = [a-b for a,b in zip(mid_jnt, mid_point)]
        pv_pos = [ a+b*4 for a,b in zip(mid_point, bend_vector) ]
        print("mid point: ", mid_point , "  | bend vector: " , bend_vector , "  | pv_pos:  " , pv_pos)

        cmds.xform(pv_ctrl, t=tuple(pv_pos), ws=True)

        # Add pv constraint
        self.connectPV_constraint(ikHandle, pv_ctrl)

        self.bake_trs_offsetParentMatrix(pv_ctrl)

        return pv_ctrl

    # connect pv ctrl to ikHandle by pole vector constraint
    def connectPV_constraint(self, ikHandle: str, pv_ctrl: str):
        cmds.poleVectorConstraint(pv_ctrl, ikHandle)

    # Connect pv ctrl to ikHandle manually, no pv constraint
    def connectPV_manual(self, ikHandle: str, pv_ctrl: str, start_jnt: str):

        # connect decompose matrix node
        start_decompose = cmds.createNode('decomposeMatrix', n='decompose_{}'.format(start_jnt))
        pv_decompose = cmds.createNode('decomposeMatrix', n='decompose_{}'.format(pv_ctrl))

        # connect them
        cmds.connectAttr('{}.worldMatrix[0]'.format(start_jnt), '{}.inputMatrix'.format(start_decompose))
        cmds.connectAttr('{}.worldMatrix[0]'.format(pv_ctrl), '{}.inputMatrix'.format(pv_decompose))

        # subtract start jnt pos from pv pos
        minus_node = cmds.createNode('plusMinusAverage')
        cmds.setAttr('{}.operation'.format(minus_node), 2)
        cmds.connectAttr('{}.outputTranslate'.format(pv_decompose), '{}.input3D[0]'.format(minus_node))
        cmds.connectAttr('{}.outputTranslate'.format(start_decompose), '{}.input3D[1]'.format(minus_node))

        # connect pv to ik_ctrl
        cmds.connectAttr('{}.output3D'.format(minus_node), '{}.poleVector'.format(ikHandle))



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
            cmds.connectAttr('{}.worldMatrix[0]'.format(temp), '{}.offsetParentMatrix'.format(transform))
            cmds.disconnectAttr('{}.worldMatrix[0]'.format(temp), '{}.offsetParentMatrix'.format(transform))

        # delete temp transform
        cmds.delete(temp)

        for attr in ["translate", "rotate", "scale"]:
            if attr != "scale":
                cmds.setAttr("{}.{}X".format(transform, attr), 0)
                cmds.setAttr("{}.{}Y".format(transform, attr), 0)
                cmds.setAttr("{}.{}Z".format(transform, attr), 0)
            else:
                cmds.setAttr("{}.{}X".format(transform, attr), 1)
                cmds.setAttr("{}.{}Y".format(transform, attr), 1)
                cmds.setAttr("{}.{}Z".format(transform, attr), 1)


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

        dup_joints.sort(key=lambda x: x.count("|"), reverse=True)

        renamed_root = None

        for jnt in dup_joints:
            short = self.shortName(jnt)
            print("short: ", short, "\n")
            short = self.clean_duplicate_suffix(short)
            print("short: ", short, "\n")

            new_name = short + suffix

            renamed_jnt = cmds.rename(jnt, new_name)

            if jnt == dup_root:
                renamed_root = renamed_jnt

        if not renamed_root:
            cmds.warning("Could not find duplicated root.")
            return []

        renamed_root = (cmds.ls(
            renamed_root,
            long=True,
            type="joint"
        ) or [renamed_root])[0]

        # Return the renamed hierachy from root to children
        renamed = cmds.listRelatives(renamed_root, allDescendents=True, type="joint") or []

        renamed.reverse()

        renamed = [renamed_root] + renamed

        return renamed


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

    @staticmethod
    def pyramid(name: str) -> str:
        cmds.curve(name=name, d=1, p=ctrlShapes.pyramid)
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

    pyramid = [
        ( -5.0, 0.0, 5.0 ),
        ( 5.0, 0.0, 5.0 ),
        ( 5.0, 0.0, -5.0 ),
        ( -5.0, 0.0, -5.0 ),
        ( -5.0, 0.0, 5.0 ),
        ( 0.0, 8.211100621552976, 0.0 ),
        ( -5.0, 0.0, -5.0 ),
        ( 5.0, 0.0, -5.0 ),
        ( 0.0, 8.211100621552976, 0.0 ),
        ( 5.0, 0.0, 5.0 )
    ]

