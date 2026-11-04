import maya.cmds as cmds # type: ignore

class IKFKUtil():

    def __init__(self):
        self.switch_attr = "ikFkSwitch"

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
        fk_joints = self.duplicate_partial_joints(joints, "_fk")
        ik_joints = self.duplicate_partial_joints(joints, "_ik")

        print("Fk joints:  ", fk_joints, "\nIk joints: ", ik_joints)
        fk_ctrls = self.buildFKLimb(limb, fk_joints)
        ik_ctrls = self.buildIKLimb(limb, ik_joints)

        jnt_pos = cmds.xform(joints[-1], query=True, t=True, ws=True)
        switch_pos = (jnt_pos[0], jnt_pos[1], jnt_pos[2]-5)

        swich_ctrl = self.createSwitchCtrl(limb, switch_pos, (0,1,0))

        self.switchIkFK(swich_ctrl, joints, fk_joints, ik_joints, fk_ctrls, ik_ctrls)

        print("Build done.\n")

    def switchIkFK(self, switch: str, joints: list[str], fk_joints: list[str], ik_joints: list[str], fk_ctrls: list[str], ik_ctrls: list[str]):

        # Add switch attribute, 0 to disable IK, 1 to enable IK
        cmds.addAttr(switch, longName=self.switch_attr, defaultValue=0, minValue=0, maxValue=1, keyable=True)

        reverse = cmds.createNode("reverse", name=switch+"_reverse")

        cmds.connectAttr(f"{switch}.{self.switch_attr}", f"{reverse}.inputX", force=True)

        for fk_joint, ik_joint, joint in zip(fk_joints, ik_joints, joints):
            constraint = cmds.parentConstraint(fk_joint, ik_joint, joint, mo=False)[0]
            weight_aliases = cmds.parentConstraint(constraint, query=True, weightAliasList=True)

            for alias in weight_aliases:
                if "fk" in alias:
                    cmds.connectAttr(f"{reverse}.outputX", f"{constraint}.{alias}", force=True)
                else:
                    cmds.connectAttr(f"{switch}.{self.switch_attr}", f"{constraint}.{alias}", force=True)
        
        # Switch the visibility of fk and ik ctrl
        for fk_ctrl in fk_ctrls:
            cmds.connectAttr(f"{reverse}.outputX", f"{fk_ctrl}.visibility", force=True)
        for ik_ctrl in ik_ctrls:
            cmds.connectAttr(f"{switch}.{self.switch_attr}", f"{ik_ctrl}.visibility", force=True)


    def createSwitchCtrl(self, limb: str, pos: tuple[float, float, float], normal: tuple[int, int, int]) -> str:
        name = limb + "_ik_fk_switch"
        switch_ctrl = createController.twoArrow(name=name, normal=normal)

        cmds.move(pos[0], pos[1], pos[2], switch_ctrl, worldSpace=True)
        self.bake_trs_offsetParentMatrix(switch_ctrl)

        return switch_ctrl

    def buildFKLimb(self, limb: str, fk_joints: list[str]) -> list[str]:
        fk_ctrls = []
        for i in range(len(fk_joints)):
            # Add FK ctrl
            fk_ctrl = createController.circle(name=fk_joints[i]+"_ctrl", r=3.0, normal=(1,0,0))
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
        ik_ctrl = createController.fourArrow(name=limb+"_ik_ctrl", normal=(1,0,0))
        cmds.matchTransform(ik_ctrl, ik_joints[-1], position=True, rotation=True)
        self.bake_trs_offsetParentMatrix(ik_ctrl)

        cmds.parent(ikHandle, ik_ctrl)

        # Add PV ctrl
        self.addPV(limb+"_pv_ctrl", ikHandle, ik_joints)

        # Add a orientation constraint to end joint, so
        # we can use ik ctrl to rotate the end joint
        cmds.orientConstraint(ik_ctrl, ik_joints[-1])

        return [ik_ctrl, pv]

    def addPV(self, name: str, ikHandle: str, ik_joints: list[str]) -> str:
        # Get joints' position
        start_jnt = cmds.xform( ik_joints[0], query=True, ws=True, rp=True )
        mid_jnt = cmds.xform( ik_joints[1], query=True, ws=True, rp=True )
        end_jnt = cmds.xform( ik_joints[2], query=True, ws=True, rp=True )

        pv_ctrl = createController.pyramid(name, normal=(0,0,1))

        # Calculate the position of PV
        # bend vector = middle_jnt - mid(end_jnt, start_jnt) 
        # pv_pos = middle_jnt + scale * bend vector
        mid_point = [(a+b)/2 for a,b in zip(end_jnt, start_jnt)]
        bend_vector = [a-b for a,b in zip(mid_jnt, mid_point)]
        pv_pos = [ a+b*5 for a,b in zip(mid_point, bend_vector) ]
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
    def duplicate_joints_hierachy(self, root_joint, suffix):
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
            short = self.clean_duplicate_suffix(short)

            new_name = short + suffix

            renamed_jnt = cmds.rename(jnt, new_name)

            if jnt == dup_root:
                renamed_root = renamed_jnt

        if not renamed_root:
            cmds.warning("Could not find duplicated root.")
            return []

        renamed_root = (cmds.ls(
            renamed_root,
            type="joint",
        ) or [renamed_root])[0]

        # Return the renamed hierachy from root to children
        renamed = cmds.listRelatives(renamed_root, allDescendents=True, type="joint") or []

        renamed.reverse()
        renamed = [renamed_root] + renamed

        return renamed

    def duplicate_partial_joints(self, joint_chain: list[str], suffix: str):
        '''
        Duplicate joint chain
        '''
        # Duplicate the whole joint hierachy
        root_joint = joint_chain[0]
        renamed_root = self.duplicate_joints_hierachy(root_joint, suffix)
        renamed_chain = [ joint + suffix for joint in joint_chain ]

        tmp_chain = renamed_chain

        # Delete children which aren't in joint chain
        while tmp_chain:
            # Delete all children of end joint
            if len(tmp_chain) == 1:
                children = cmds.listRelatives(tmp_chain[0], children=True, type="joint") or []
                for child in children:
                    cmds.delete(child)
                break

            children = cmds.listRelatives(tmp_chain[0], children=True, type="joint") or []
            for child in children:
                if child not in renamed_chain:
                    cmds.delete(child)
            tmp_chain = tmp_chain[1:]

        
        return renamed_chain


    # Add an attribute of "message" type to node
    def create_message_attr(self, node, attr, multi=False):
        if not cmds.attributeQuery(attr, node=node, exists=True):
            cmds.addAttr(node, longName=attr, attributeType="message", multi=multi)

    def register_limb_rig_message(self, node_name, switch_ctrl, fk_ctrls, fk_joints, ik_ctrl, pv_ctrl, ik_joints):
        '''
        Create a "network" type node to store the reference to switch ctrl, fk ctrl and joints, ik ctrl and joints, pv ctrl
        This function is used to find their info when switch ik and fk seamlessly
        '''

        meta = cmds.createNode("network", name=node_name)

        self.create_message_attr(meta, "switch_ctrl")
        self.create_message_attr(meta, "ik_ctrl")
        self.create_message_attr(meta, "pv_ctrl")

        self.create_message_attr(meta, "fk_ctrls", multi=True)
        self.create_message_attr(meta, "fk_joints", multi=True)
        self.create_message_attr(meta, "ik_joints", multi=True)

        self.create_message_attr(switch_ctrl, "rig_meta")

        cmds.connectAttr(switch_ctrl+".message", meta+".switch_ctrl")
        cmds.connectAttr(ik_ctrl+".message", meta+".ik_ctrl")
        cmds.connectAttr(pv_ctrl+".message", meta+".pv_ctrl")

        for i, (ctrl, joint) in enumerate(zip(fk_ctrls, fk_joints)):
            cmds.connectAttr(ctrl+".message", "{}.fk_ctrls[{}]".format(meta, i))
            cmds.connectAttr(joint+".message", "{}.fk_joints[{}]".format(meta, i))

        for i, joint in enumerate(ik_joints):
            cmds.connectAttr(joint+".message", "{}.ik_joints[{}]".format(meta, i))

        # Find meta from switch ctrl by adding a reference to meta
        self.create_message_attr(switch_ctrl, "rig_meta", multi=)
        cmds.connectAttr(meta+".message", switch_ctrl)

        return meta

    # Origin: https://gist.github.com/vshotarov/5f28441fab335ccf1ee65d2563f02488
    def ikFkSwitch_sameOrient(self):
        switch_ctrl = cmds.ls(sl=True)[0]
        if not switch_ctrl:
            cmds.warning("Selecting switch controller before switching ik and fk")

        switch_attr = cmds.getAttr(f"{switch_ctrl}.{self.switch_attr}")
        if not switch_attr:
            cmds.warning("Can't find \"ikFkSwitch\" attribute in the selected controller")


        if switch_attr != 0:
            # From fk to ik

        else:
            # From ik to fk





        


class createController():

    @staticmethod
    def circle(name: str, r: float, normal: tuple[float, float, float]) -> str:
        cmds.circle(name=name, radius=r, normal=normal)
        return name

    @staticmethod
    def fourArrow(name: str, normal: tuple[int, int, int]) -> str:
        cmds.curve(name=name, d=1, p=ctrlShapes.four_arrow)
        createController.changeCurveNormal(name, normal=normal)
        return name

    @staticmethod
    def twoArrow(name: str, normal: tuple[int, int, int]) -> str:
        cmds.curve(name=name, d=1, p=ctrlShapes.two_arrow)
        createController.changeCurveNormal(name, normal)
        return name

    @staticmethod
    def pyramid(name: str, normal: tuple[int, int, int]) -> str:
        cmds.curve(name=name, d=1, p=ctrlShapes.pyramid)
        createController.changeCurveNormal(name, normal)
        return name

    @staticmethod
    def changeCurveNormal(curve: str, normal: tuple[int, int, int]):
        if normal == (0,1,0):       # the normal of curve is Y by default
            return
        elif normal == (1,0,0):
            cmds.rotate(0,0,90, f"{curve}.cv[*]", relative=True, objectSpace=True)
        elif normal == (0,0,1):
            cmds.rotate(90,0,0, f"{curve}.cv[*]", relative=True, objectSpace=True)
        else:
            pass

class ctrlShapes():

    four_arrow = [
        ( 0.0, 0.0, -5.0 ),
        ( -2.0, 0.0, -3.0 ),
        ( -1.0, 0.0, -3.0 ),
        ( -1.0, 0.0, -1.0 ),
        ( -3.0, 0.0, -1.0 ),
        ( -3.0, 0.0, -2.0 ),
        ( -5.0, 0.0, 0.0 ),
        ( -3.0, 0.0, 2.0 ),
        ( -3.0, 0.0, 1.0 ),
        ( -1.0, 0.0, 1.0 ),
        ( -1.0, 0.0, 3.0 ),
        ( -2.0, 0.0, 3.0 ),
        ( 0.0, 0.0, 5.0 ),
        ( 2.0, 0.0, 3.0 ),
        ( 1.0, 0.0, 3.0 ),
        ( 1.0, 0.0, 1.0 ),
        ( 3.0, 0.0, 1.0 ),
        ( 3.0, 0.0, 2.0 ),
        ( 5.0, 0.0, 0.0 ),
        ( 3.0, 0.0, -2.0 ),
        ( 3.0, 0.0, -1.0 ),
        ( 1.0, 0.0, -1.0 ),
        ( 1.0, 0.0, -3.0 ),
        ( 2.0, 0.0, -3.0 ),
        ( 0.0, 0.0, -5.0 )
    ]

#    two_arrow = [
#        ( -10.0, 0.0, -15.0 ),
#        ( -20.0, 0.0, 0.0 ),
#        ( -10.0, 0.0, 15.0 ),
#        ( -10.0, 0.0, 5.0 ),
#        ( 10.0, 0.0, 5.0 ),
#        ( 10.0, 0.0, 15.0 ),
#        ( 20.0, 0.0, 0.0 ),
#        ( 10.0, 0.0, -15.0 ),
#        ( 10.0, 0.0, -5.0 ),
#        ( -10.0, 0.0, -5.0 ),
#        ( -10.0, 0.0, -15.0 )
#    ]
    two_arrow = [
        ( -2.0, 0.0, -3.0 ),
        ( -4.0, 0.0, 0.0 ),
        ( -2.0, 0.0, 3.0 ),
        ( -2.0, 0.0, 1.0 ),
        ( 2.0, 0.0, 1.0 ),
        ( 2.0, 0.0, 3.0 ),
        ( 4.0, 0.0, 0.0 ),
        ( 2.0, 0.0, -3.0 ),
        ( 2.0, 0.0, -1.0 ),
        ( -2.0, 0.0, -1.0 ),
        ( -2.0, 0.0, -3.0 )
    ]

    pyramid = [
        ( -1.0, 0.0, 1.0 ),
        ( 1.0, 0.0, 1.0 ),
        ( 1.0, 0.0, -1.0 ),
        ( -1.0, 0.0, -1.0 ),
        ( -1.0, 0.0, 1.0 ),
        ( 0.0, 1.6, 0.0 ),
        ( -1.0, 0.0, -1.0 ),
        ( 1.0, 0.0, -1.0 ),
        ( 0.0, 1.6, 0.0 ),
        ( 1.0, 0.0, 1.0 )
    ]

