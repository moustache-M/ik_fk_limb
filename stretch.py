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
        pass

    def getOriginLimbLength(self, ik_joints: list[str]) -> double:
        return 0.0

    def getStretchSquashLength(self, root_locator: str, ik_ctrl: str) -> double:
        return 0.0

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



    
