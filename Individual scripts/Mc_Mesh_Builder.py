import os
import json
import maya.cmds as cmds

#testpath = input("Mc Model .json file path \n")
Warned=False

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
    
    #Check transformation are freezed, this is a maya limitation on calculating face normals
    #The check ignore transforms that results in incorrect normal direction.
    CurrentRot = cmds.xform(Object,q=True,ro=True)
    if not CurrentRot == [0,0,0]:
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

def constructCube() -> str:
    """Generates the cube group

    Returns:
        str: Cube group name
    """

    faces = {"down": [[0, -0.5, 0], [180, 0, 0]],
             "up": [[0, .5, 0], [0, 0, 0]],
             "north": [[0, 0, 0.5], [90, 0, 180]],
             "south": [[0, 0, -0.5], [-90, 0, 0]],
             "west": [[0.5, 0, 0], [-90, -90, 0]],
             "east": [[-0.5, 0, 0], [-90, 90, 0]]}
    cube = []

    for direction, translation in faces.items():
        plane = cmds.polyPlane(n=str(direction), sx=1, sy=1)[0]
        cmds.move(translation[0][0], translation[0][1], translation[0][2], plane)
        cmds.rotate(translation[1][0], translation[1][1], translation[1][2], plane)
        cube.append(plane)

    return cmds.rename(cmds.group(cube), "block#")

def filterPath(path) -> str:
    return os.path.dirname(path)

def filename(path):
    filename = os.path.basename(path)
    return os.path.splitext(filename)

def removeLast(path: str) -> str:
    split = path.split("\\")
    split.pop(-1)

    return str("\\".join(split))

def loadJson(path) -> dict:
    with open(path, "r") as loaded:
        load = json.load(loaded)
    return load


def buildMesh(path,DelHis=False):

    def createShader(shaderType:str) -> str:
        """
        Generate the shader node, connect it to a shading group 
        """
        shaderName = cmds.shadingNode(shaderType, asShader=True)
        sgName = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=(shaderName + "SG"))
        cmds.connectAttr(shaderName + ".outColor", sgName + ".surfaceShader")
        return str(shaderName)

    def MathScale(a: list, b: list) -> list:
        for aa, bb in zip(a, b):
            yield (bb-aa)

    def mathTrans(a: list, b: list) -> list:
        for aa, bb in zip(a, b):
            yield (aa+bb)/2

    def remap(x, in_min, in_max, out_min, out_max):
        return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

    def WarnOnce(message:str):
        global Warned
        if Warned:
            return
        Warned = True
        cmds.warning(message)

    Json = loadJson(path)

    try:
        textureDb={}
        for name,f in Json["textures"].items():    
            f:str
            
            #Skip if particle
            if str(name) == "particle":
                continue
            
            #Generate Lambert material.
            split = f.split("/")[-1]
            if cmds.objExists(split):
                cmds.warning(f"{split} already exists, Skipping")
                continue
            
            cmds.rename(createShader("lambert"),split)
            textureDb[name]=split
    except:
        cmds.warning(f"No textures found, Skipping")

    ObjTUv = []
    
    #Generate the mesh
    Block = []
    for i in Json["elements"]:
        i: dict
        
        # Create cube
        Cube = constructCube()
       
        # Transform it into correct position
        Scale = list(MathScale(i["from"], i["to"]))
        Transform = list(mathTrans(i["from"], i["to"]))
        cmds.scale(Scale[0], Scale[1], Scale[2], Cube)
        cmds.move(Transform[0], Transform[1], Transform[2], Cube)
        
        # Remove un needed faces.
        for x in cmds.listRelatives(Cube):
            currentFace = (f"{Cube}|{x}")
            if x not in i["faces"].keys():
                cmds.delete(currentFace)
                continue
            
            # Uv faces
            if "uv" in i["faces"][x]:
                uv:list = i["faces"][x]["uv"]
                uv = [remap(i,0,16,0,1) for i in uv]

                cmds.polyEditUV(currentFace+".map[0]", relative=False, uValue=uv[0], vValue=uv[1])
                cmds.polyEditUV(currentFace+".map[3]", relative=False, uValue=uv[2], vValue=uv[3])
                cmds.polyEditUV(currentFace+".map[2]", relative=False, uValue=uv[0], vValue=uv[3])
                cmds.polyEditUV(currentFace+".map[1]", relative=False, uValue=uv[2], vValue=uv[1])
            else:
                ObjTUv.append(currentFace)
                WarnOnce("No uv found, Skipping")
            
            #Assign faces to correct Material
            try:
                texture = textureDb.get(str(i["faces"][x]["texture"]).replace("#",""))
                cmds.select(currentFace)
                cmds.hyperShade(assign=texture)
            except:
                cmds.warning("Failed to assign material")
        global Warned
        Warned = False      
        
        if "rotation" in i.keys():
            cmds.setAttr(Cube+".rotatePivot", float(i["rotation"]["origin"][0]), float(i["rotation"]["origin"][1]), float(i["rotation"]["origin"][2]), type="float3")
            if i["rotation"]["axis"] == "x":
                cmds.setAttr(Cube+".rotateX", i["rotation"]["angle"])
            elif i["rotation"]["axis"] == "y":
                cmds.setAttr(Cube+".rotateY", i["rotation"]["angle"])
            elif i["rotation"]["axis"] == "z":
                cmds.setAttr(Cube+".rotateZ", i["rotation"]["angle"])
          
        Block.append(Cube)

    #Combine complete mesh
    cmds.select(Block)
    Mesh = cmds.polyUnite(cmds.ls(sl=True), n=filename(path)[0])[0]
    cmds.polyMergeVertex(Mesh, d=0.0001)
    
    if not len(ObjTUv) == 0:
        cmds.refresh()
        startProjection(Mesh)
    else:
        #Fix flipped uv's
        cmds.select(cmds.polyListComponentConversion(Mesh, uvs=True))
        cmds.setAttr(Mesh+".uvPivot", 0, 0, type="float2")
        cmds.polyFlipUV(cmds.ls(sl=True),ft=1)

    if DelHis:
        cmds.delete(Mesh, ch=True)
    
    

buildMesh(r"D:\Important\Desktop\model.json",True)
