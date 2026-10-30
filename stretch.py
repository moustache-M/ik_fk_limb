import maya.cmds as cmds


class StretchSquashUtil():
    def build(self, limb, primary_axis, switch_ctrl, ik_joints, ik_ctrl):
        '''
        Add stretch and squash ability to limb
        Args:
            limb: which limb to add
            primary_axis: the direction of limb to stretch or sqaush.
                            It points from root joint to end joint of limb.
            switch_ctrl: switch ctrl, add stretch and squash attribute to it
            
            ik_joints: ik joints, used to calculate length
            ik_ctrl:   ik ctrl, used to calculate length
        '''

        # Place locator in the root joint
        root_jnt_pos = cmds.xform(ik_joints[0], query=True, p=True, ws=True)
        root_locator = cmds.spaceLocator(name=ik_joints[0]+"locator", p=root_jnt_pos)

        # Get original limb length
        origin_length = 0.0
        origin_length += abs(cmds.getAttr("{}.translate{}".format(ik_joints[1], primary_axis)))
        origin_length += abs(cmds.getAttr("{}.translate{}".format(ik_joints[2], primary_axis)))

        # Get stretch limb length
        distance_node = cmds.createNode("distanceBetween", name=limb+"_stretch_distance")

        cmds.connectAttr(root_locator+".worldMatrix[0]", distance_node+".inMatrix1")
        cmds.connectAttr(root_locator+".worldMatrix[0]", distance_node+".inMatrix2")

        # Get ratio of origin and stretch length 
        divide_node = cmds.createNode("multiplyDivide", name=limb+"_divide")
        cmds.setAttr(f"{divide_node}.operation", 2)     # operation: divide
        cmds.connectAttr(f"{distance_node}.distance", f"{divide_node}.input1X")
        cmds.setAttr(f"{divide_node}.input2X", origin_length)

        # Set condition node and use switch_ctrl attribute to control its operation
        # Further to determine whether stretch, squash or do nothing
        condition_node = cmds.createNode("condition")
        # cmds.setAttr(f"{condition_node}.operation", )
        cmds.connectAttr(f"{divide_node}.outputX", f"{condition_node}.firstTerm")
        cmds.setAttr(f"{condition_node}.secondTerm", 1)

        cmds.connectAttr(f"{divide_node}.outputX", f"{condition_node}.colorIfTrueR")
        cmds.setAttr(f"{condition_node}.colorIfFalseR", 1)

        cmds.addAttr(switch_ctrl, longName="STRETCH")




    def getStretchSquashLength(self, limb: str, root_locator: str, ik_ctrl: str) -> float:

        return cmds.getAttr( distance_node + ".distance" )

    def addAttr()

    """
    ratio = (stretch length / original legnth) 
    if ratio > 1:
        scale of first two joints = ratio
    else if ratio == 1:
        nothing
    else if ratio < 1:
        scale of first two joints = ratio

    condtion node: 0  Equal                 switch attr:    nothing
                   1  Not Equal                             stretch and squash
                   2  Greater Than                          stretch
                   3  Greater Or Equal                      nothing
                   4  Less Than                             squash
                   5  Less or Equal                         nothing

    Only enable it in ik mode by blend node:
    switch.ikfk     ->      blend.blender
    conditon node   ->      blend.color1R
    1.0             ->      blend.color2R
    """



    
