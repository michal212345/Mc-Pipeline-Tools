import maya.cmds as cmds
import maya.mel as mel

def ConstraintLocator(face):
    locator = cmds.spaceLocator()
    cmds.select(face,locator)
    mel.eval("PointOnPolyConstraint;")

selection = cmds.ls(sl=True,fl=True)
print(selection)

if len(selection) > 1:
    for i in selection:
        nodetype = cmds.objectType(i)
        if not nodetype == "mesh":
            cmds.error("No mesh selected")
        else:
            ConstraintLocator(i)
else:
    nodetype = cmds.objectType(selection)
    if not nodetype == "mesh":
        cmds.error("No mesh selected")
    else:
        ConstraintLocator(selection)
