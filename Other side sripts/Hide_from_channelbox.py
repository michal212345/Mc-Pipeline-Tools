from maya import cmds
try:
    if not len(n:=cmds.ls(sl=True)) == 0:
        for node in n:
            cmds.setAttr(node + ".ihi", 0)
except Exception as e:
    cmds.error(f"Failed to hide from channel box. \n Reason: {e}")