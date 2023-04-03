import maya.cmds as cmds
try:
    from PIL import Image
except:
    cmds.error("You need to install Pillow using Mayapy.")

def has_transparency(img:Image.Image):
    if img.info.get("transparency", None) is not None:
        return True
    if img.mode == "P":
        transparent = img.info.get("transparency", -1)
        for _, index in img.getcolors():
            if index == transparent:
                return True
    elif img.mode == "RGBA":
        extrema = img.getextrema()
        if extrema[3][0] < 255:
            return True

    return False

for i in cmds.ls(sl=True):
    try:
        if len(cmds.listConnections(i+".color")) == 1:
            file = cmds.listConnections(i+".color")[0]
            filePath = cmds.getAttr(file+".fileTextureName")
            if has_transparency(Image.open(filePath)):
                cmds.connectAttr(file+".outTransparency",i+".transparency")
    except:
        continue