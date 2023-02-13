import maya.cmds as cmds

for i in cmds.ls(type="file"):
    cmds.setAttr(i+".ft",0)