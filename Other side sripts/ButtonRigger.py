import maya.cmds as cmds
import maya.mel as mel

def ConstraintLocator(face):
    locator = cmds.spaceLocator()
    cmds.select(face,locator)
    mel.eval('doCreatePointOnPolyConstraintArgList 2 {   "0" ,"0" ,"0" ,"1" ,"" ,"1" ,"0" ,"0" ,"0" ,"0" };')

selection = cmds.ls(sl=True,fl=True)

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
