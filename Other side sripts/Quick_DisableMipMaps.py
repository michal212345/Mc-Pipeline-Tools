import maya.cmds as cmds

try:
    for i in cmds.ls(type="file"):
        cmds.setAttr(i+".ft",0)
except:
    cmds.error("There are no file nodes in your scene!")