from maya import cmds
for node in cmds.ls(sl=True):
    cmds.setAttr(node + ".ihi", 0)