import maya.cmds as cmds
import maya.mel as mel

def optimizeEdges(Object:str,lowA:int,HighA:int):
    cmds.selectMode(object=True)
    cmds.select(cmds.polyListComponentConversion(Object,te=True))
    cmds.polySelectConstraint( m=3, t=0x8000, a=True, ab=(lowA, HighA) )
    HardEdges = cmds.ls(sl=True)
    cmds.polySelectConstraint(m=0, a=False)
    cmds.select(HardEdges)
    mel.eval("GrowLoopPolygonSelectionRegion;SelectEdgeLoopSp;InvertSelection;")
    cmds.polyDelEdge(cmds.ls(sl=True),cv=True)

if __name__ == "__main__":
    for i in cmds.ls(sl=True):
        optimizeEdges(i,45,91)