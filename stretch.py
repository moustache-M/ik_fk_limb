import maya.cmds as cmds


class StretchSquashUtil():
    def build(self, limb, primary_axis, switch_ctrl, switch_ik_fk_attr, ik_joints, ik_ctrl):
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

        cmds.addAttr(switch_ctrl, longName="stretchMode", attributeType='enum', enumName="None:Stretch_Squash:Stretch:Squash")

        # Map stretch mode to condition operation number
        # None: 0, Stretch_Squash: 1,   Stretch: 2,   Squash: 4 
        mode_choice = cmds.createNode("choice", name=f"{limb}_stretch_squash_mode_choice")
        cmds.setAttr(f"{mode_choice}.input[0]", 0)
        cmds.setAttr(f"{mode_choice}.input[0]", 1)
        cmds.setAttr(f"{mode_choice}.input[0]", 2)
        cmds.setAttr(f"{mode_choice}.input[0]", 4)

        # Siwtch ctrl attr -> choice node selector
        cmds.connectAttr(f"{switch_ctrl}.stretchMode", f"{mode_choice}.selector")
        # Choice node selector  ->  conditon node operation
        cmds.connectAttr(f"{mode_choice}.output", f"{condition_node}.operation")

        # Only stretch in IK mode by blend node
        blend = cmds.createNode("blendColors", name=limb+"_stretch_blend")
        cmds.connectAttr(f"{switch_ctrl}.{switch_ik_fk_attr}", f"{blend}.blender")
        cmds.connectAttr(f"{condition_node}.outColorR", f"{blend}.color1R")
        cmds.setAttr(f"{blend}.color2R", 1.0)


        # Scale only first and second ik joints
        # Joint 3 is the end joint and does not need scale 
        scale_attr = "scale" + primary_axis
        cmds.connectAttr(f"{blend}.outputR", f"{ik_joints[0]}.{scale_attr}")
        cmds.connectAttr(f"{blend}.outputR", f"{ik_joints[1]}.{scale_attr}")


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



    
