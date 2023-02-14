import maya.cmds as cmds
import json
import re 

def getNormalDirection(face:str) -> list:
    """Unpacks the normals direction from given face

    Args:
        face (str): Mesh.f[*]

    Returns:
        list: Returns a list of three vectors between -1 and 1
    """
    polyInfo = cmds.polyInfo(face, fn=True)
    polyInfoArray = re.findall(r"[\w.-]+", polyInfo[0])
    return [float(polyInfoArray[2].replace("-","")),float(polyInfoArray[3].replace("-","")),float(polyInfoArray[4].replace("-",""))]

def listSimilarFaces(object:str) -> dict:
    """Return a list of similarly facing faces sorted by Direction and all faces facing it.

    Args:
        object (str): The mesh
    Returns:
        list: [Direction],[Face numbers]
    """
    faces = cmds.ls(cmds.polyListComponentConversion(object, tf=True),fl=True)
    data={}
    for nr,i in enumerate(faces):
        data[nr] = getNormalDirection(i)

    TempDict = {}
    for key,value in data.items():
        if str(value) not in TempDict.keys():
            TempDict[str(value)] = []

        #Somehow that worked
        TempDict[str(value)].append(str(key))

    return TempDict

def ResDirection(RX:float,RY:float,RZ:float) -> str:
    """Resolve Normal direction"""
   
    if RX == 1:
        return "x"
    elif RY == 1:
        return "y"
    elif RZ == 1:
        return "z"
    else:
        cmds.error("couldn't resolve direction." + f" Direction: {RX}, {RY}, {RZ}")


def startProjection(Object:str):
    
    if type(Object) == list:
        Object = Object[-1]
    
    #Check transformation are freezed, this is a maya limitation on calculating face normals
    #The check ignore transforms that results in incorrect normal direction.
    CurrentRot = cmds.xform(Object,q=True,ro=True)
    if not CurrentRot == [0,0,0]:
        FrzTrans = cmds.confirmDialog( title='Confirm', message='Mesh needs to be Freeze Transformed', button=['Ok','No'], defaultButton='Ok', cancelButton='No', dismissString='No' )
        if FrzTrans == "No":
            cmds.error("Mesh needs to be freeze transformed before starting projection.")
        else:
            cmds.makeIdentity(Object, apply=True )
            cmds.refresh()
    
    #Collect face and direction
    data = listSimilarFaces(Object)

    #Calculate the Uvs in groups of faces that face the same direction result is connected uvs.           
    for Cord,faces in data.items():
        faceList = []
        Cord:list = json.loads(Cord)
        direction = ResDirection(Cord[0],Cord[1],Cord[2])
        for face in faces:
            faceList.append(f"{Object}.f[{face}]")
        Projection = cmds.polyProjection(faceList,type='Planar',md=direction)
        cmds.setAttr(Projection[0]+".projectionWidth",16)
        cmds.setAttr(Projection[0]+".projectionHeight",16)

if __name__ == "__main__":
    if len(cmds.ls(sl=True)) == 0:
        cmds.error("No selection.")
    else:
        startProjection(cmds.ls(sl=True))