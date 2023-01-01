import maya.mel as mel
import maya.cmds as cmds

if len(cmds.ls(sl=True)) == 0:
    cmds.error("No faces selected")

nodetype = cmds.objectType(cmds.ls(sl=True,tl=1))
if not nodetype == "Mesh":
    faces = cmds.ls(cmds.polyListComponentConversion(cmds.ls(sl=True),tf=True),fl=True)
else:
    faces = cmds.ls(sl=True,fl=True)


for i in faces:
    cmds.select(i)
    mel.eval('texNormalProjection 1 1 "" ;')