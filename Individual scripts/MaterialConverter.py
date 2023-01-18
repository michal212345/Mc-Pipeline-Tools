import maya.cmds as cmds

#######
# If you follow the patterns, all basic components will work.
####### 

## Basic ui name
MATERIALCOMMANDS={
    # Ui name   # The mell command to create material, use echo to find it.
    "Redshift" : 'RedshiftMaterial',
    "Arnold" : 'aiStandardSurface',
    "Renderman" : 'PxrSurface'
}

PLUGINLIST={
    # Ui name   # Plugin name
    "Redshift": "redshift4maya.mll",
    "Arnold": "mtoa.mll",
    "Renderman":"RenderMan_for_Maya.py"
}

## These need node names, below... ##

MATERIALALPHA={
                        # Node connection for Opacity
    "RedshiftMaterial" : ".opacity_color",
    "aiStandardSurface" : ".opacity",
    "PxrSurface":".presence"
}

MATERIALDIFFUSE={
                        #Node connection for Diffuse/Color
    "RedshiftMaterial":".diffuse_color",
    "aiStandardSurface":".baseColor",
    "PxrSurface":".diffuseColor"
}

MATERIALSPECULAR={
                        #Node connection for Specular/reflection
    "RedshiftMaterial":".refl_weight",
    "aiStandardSurface":".specular",
    "PxrSurface":".specularRoughness"
}

SHADINGNODE={
    # Node name          #Render engine Shading engine input, find in hypershade.
    "RedshiftMaterial" : ".rsSurfaceShader",
    "aiStandardSurface" : ".aiSurfaceShader",
    "PxrSurface":".rman__surface"
}

FILEMIPMAP={
                        #Render engine specific mipmap toggle
    "RedshiftMaterial": ".rsFilterEnable",
    "aiStandardSurface": ".aiFilter",
    "aiStandardSurface": ".rman__filter"
}

# Do not add render engine unless you have edited special behaviour code to include that new engine.
CUSTOMBEHAVIOUR=["Redshift","Arnold","Renderman"]

## Dont change.
EMPTY = [""," ",None]

###
# Ui code
###

def deleteIfOpen():  
    if cmds.window('MatConverter', exists=True):
        cmds.deleteUI('MatConverter')

def mayaWindow():
    def addDropDown(identifier,label,items,cc="None"):
        cmds.optionMenu(identifier,label=label,cc=cc)
        for i in items:
            cmds.menuItem(label = i)
    
    #Let user define the suffix of Spec and normal
    cmds.window('MatConverter', title="Multi-purpose material converter", width=300, height=200, maximizeButton=False, resizeToFitChildren=True)
    cmds.columnLayout(adjustableColumn=True)
    
    cmds.rowLayout(numberOfColumns=2, adjustableColumn2=2, columnWidth2=[120, 70],columnAlign2=['left', 'left'], columnAttach2=['left', 'left'])
    cmds.text("From:")
    addDropDown("FromMat","",["phong","phongE","lambert","blinn"])
    cmds.setParent('..')
    cmds.setParent('..')
    
    cmds.rowLayout(numberOfColumns=2, adjustableColumn2=2, columnWidth2=[120, 70],columnAlign2=['left', 'left'], columnAttach2=['left', 'left'])
    cmds.text("To:")
    addDropDown("ToMat","",CUSTOMBEHAVIOUR)
    cmds.setParent('..')
    cmds.setParent('..')

    cmds.rowLayout(numberOfColumns=4, adjustableColumn4=4, columnWidth4=[120, 120, 120, 120],columnAlign4=['left', 'left', 'left', 'left'], columnAttach4=['left', 'left', 'left', 'left'])
    cmds.checkBox('proxymode',l='Create Proxy',v=True)
    cmds.checkBox('enableAlpha',l='Enable alpha',v=True)
    cmds.checkBox('disableMipMap',l='Disable mipmaps',v=True)
    cmds.checkBox('EnableExtra',l="Do Extra",v=True)
    cmds.setParent('..')
    cmds.setParent('..')
    cmds.setParent('..')
    cmds.setParent('..')
    
    cmds.rowLayout(numberOfColumns=2, adjustableColumn2=2, columnWidth2=[120, 120],columnAlign2=['left', 'right'], columnAttach2=['left', 'right'])
    cmds.button(l="Close",c="deleteIfOpen()")
    cmds.button(l="Start",c="start()")

    cmds.showWindow('MatConverter')

###
# Script code
###

def getSelection(Mat:str) -> list:

    """
    Filters selection to material,
    Also converts mesh/transform selection to material.

    returns list of materials
    """

    #Grab selection nodetype
    nodetype = cmds.objectType(cmds.ls(sl=True,tl=1))

    #Check node type and return Material
    if not Mat == nodetype:
        if nodetype == "mesh" or nodetype == "transform":
            theNodes = cmds.ls(sl = True, dag = True, s = True)
            shadeEng = cmds.listConnections(theNodes , type = "shadingEngine")
            selection = cmds.ls(cmds.listConnections(shadeEng ), materials = True)
    else:
        selection = cmds.ls(sl=True, type=Mat)

    #Check if selection isnt nothing
    if len(selection) == 0:
        print("No selection or valid selection was made.")
        return
    
    #Remove lambert1 if in selection
    #Its to prevent maya from freaking out... You shouldn't really touch Lambert1
    try:
        if "lambert1" in str(selection):
            selection.remove("lambert1")
    except:
        None
    
    # Return the slection as a list.
    else:
        if type(selection) == list:
            return selection
        elif type(selection) == str:
            temp = []
            temp.append(selection)
            return temp

def hasConnection(Mat,socket) -> bool:
    """
    Check if there's a connection in specified socket.
    Error handle to return false
    """

    try:
        return bool(cmds.listConnections(Mat+socket,d=True)[0])
    except:
        return False

def createShader(shaderType:str) -> str:
    """
    Generate the shader node, connect it to a shading group 
    """
    shaderName = cmds.shadingNode(shaderType, asShader=True)
    sgName = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=(shaderName + "SG"))
    cmds.connectAttr(shaderName + ".outColor", sgName + ".surfaceShader")
    return str(shaderName)

def convFromYtoX(Material,MatX):
    """
    Convert material from Y to X using nodecast.
    """
    cmds.nodeCast(Material,MatX,disconnectUnmatchedAttrs=True,f=True)

def connectDiffuse(fileNode,Material,oldMat):
    """
    Connect diffuse/color to the new material.
    If there's no connection getAttr from oldMat it and setAttr it to the new Mat
    """
    if hasConnection(Material,str(MATERIALDIFFUSE.get(Material))):
        if cmds.checkBox("disableMipMap",q=True,v=True) == True:
            cmds.setAttr(fileNode+".filterType",0)
        cmds.connectAttr(fileNode+".outColor",str(Material)+MATERIALDIFFUSE.get(cmds.nodeType(Material)))
    else:
        try:
            colorList = list(cmds.getAttr(oldMat+".color")[0])
            cmds.setAttr(Material+MATERIALDIFFUSE.get(cmds.nodeType(Material)),colorList[0],colorList[1],colorList[2])
        except:
            print("Failed to transfer Diffuse/Color attribute to new Material.")           

def connectAlpha(fileNode,Material,oldMat):
    """
    Attempt to connect single channel of alpha in texture to the new to the new material as multichannel: Alpha to Alpha(R,G,B)
    Error handle to try and connect alpha as a single channel: Alpha to Alpha
    """
    def connectAttr(*args):
        """
        No error printing connectAttr
        """
        try:
            cmds.connectAttr(args)
        except:
            None
    if hasConnection(Material,str(MATERIALALPHA.get(Material))):
        try:
            cmds.connectAttr(fileNode+".outAlpha",str(Material)+MATERIALALPHA.get(cmds.nodeType(Material))+"R")
            cmds.connectAttr(fileNode+".outAlpha",str(Material)+MATERIALALPHA.get(cmds.nodeType(Material))+"G")
            cmds.connectAttr(fileNode+".outAlpha",str(Material)+MATERIALALPHA.get(cmds.nodeType(Material))+"B")
        except Exception as f:
            print(f"Failed to connect alpha falling back to single connection, Error: {f}")
            connectAttr(fileNode+".outAlpha",Material+MATERIALALPHA.get(cmds.nodeType(Material)))
    else:
        try:
            colorList = list(cmds.getAttr(oldMat+".transparency")[0])
            cmds.setAttr(Material+MATERIALALPHA.get(cmds.nodeType(Material)),colorList[0],colorList[1],colorList[2])        
        except:
            print("Failed to transfer Alpha attribute to new Material.")

def disableMipMaps(fileNode,NewMat):
    """
    Attempt to disable mipmap of the filenode.
    """
    try:
        cmds.setAttr(fileNode+FILEMIPMAP.get(cmds.nodeType(NewMat)),0)
    except:
        print("No filenode to mipmap! SKipping.")

def connectSpecial(mat,NewMat,To):
    """
    Special behaviour, Connecting objects that might be a bit more work then reconnecting.
    """
    # All custom actions happen here. Code them below

    if To == "Redshift":
        if hasConnection(mat,".ambientColor"):
            filenode = cmds.listConnections(mat+".ambientColor",d=True)[0]
            cmds.connectAttr(filenode+".outColor",NewMat+".overall_color")
        
        if hasConnection(mat,".normalCamera"):
            filenode = cmds.listConnections(mat+".normalCamera",d=True)[0]
            Displacement = cmds.shadingNode("RedshiftBumpMap",asUtility=True)
            cmds.setAttr(Displacement+".inputType",1)
            cmds.connectAttr(filenode+".outColor",Displacement+".input")
            cmds.setAttr(Displacement+".scale",.4)
            cmds.connectAttr(Displacement+".out",NewMat+".bump_input")
        
        if hasConnection(mat,".reflectivity"):
            filenode = cmds.listConnections(mat+".reflectivity",d=True)[0]
            cmds.connectAttr(filenode+".outColorR",str(NewMat)+str(MATERIALSPECULAR.get(cmds.nodeType(NewMat))))
            if cmds.checkBox("disableMipMap",q=True,v=True) == True:
                disableMipMaps(filenode,NewMat)
    
    elif To == "Arnold":
        if hasConnection(mat,".reflectivity"):
            filenode = cmds.listConnections(mat+".reflectivity",d=True)[0]
            cmds.connectAttr(filenode+".outColorR",NewMat+MATERIALSPECULAR.get(cmds.nodeType(NewMat)))
            if cmds.checkBox("disableMipMap",q=True,v=True) == True:
                disableMipMaps(filenode,NewMat)

        if hasConnection(mat,".ambientColor"):
            filenode = cmds.listConnections(mat+".ambientColor",d=True)[0]
            basecolor = cmds.listConnections(NewMat+".baseColor",d=True)[0]
            multipley = cmds.shadingNode("aiMultiply",asUtility=True)
            cmds.connectAttr(basecolor+".outColor",multipley+".input2")
            cmds.connectAttr(filenode+".outColor",multipley+".input1")
            cmds.connectAttr(multipley+".outColor",NewMat+".baseColor",f=True)

        if hasConnection(mat,".normalCamera"):
            filenode = cmds.listConnections(mat+".normalCamera",d=True)[0]
            Displacement = cmds.shadingNode("aiNormalMap",asUtility=True)
            cmds.connectAttr(filenode+".outColor",Displacement+".normal")
            cmds.setAttr(Displacement+".strength",.4)
            cmds.connectAttr(Displacement+".outValue",NewMat+".normalCamera",f=True)

    elif To == "Renderman":
        if hasConnection(mat,".reflectivity"):
            filenode = cmds.listConnections(mat+".reflectivity",d=True)[0]
            cmds.connectAttr(filenode+".outColorR",NewMat+MATERIALSPECULAR.get(cmds.nodeType(NewMat)))
            if cmds.checkBox("disableMipMap",q=True,v=True) == True:
                disableMipMaps(filenode,NewMat)

        if hasConnection(mat,".ambientColor"):
            filenode = cmds.listConnections(mat+".ambientColor",d=True)[0]
            basecolor = cmds.listConnections(NewMat+".diffuseColor",d=True)[0]
            multipley = cmds.shadingNode("PxrBlend",asUtility=True)
            cmds.connectAttr(basecolor+".outColor",multipley+".bottomRGB")
            cmds.setAttr(multipley+".operation",18)
            cmds.connectAttr(filenode+".outColor",multipley+".topRGB")
            cmds.connectAttr(multipley+".resultRGB",NewMat+".diffuseColor",f=True)

        if hasConnection(mat,".normalCamera"):
            filenode = cmds.listConnections(mat+".normalCamera",d=True)[0]
            Displacement = cmds.shadingNode("PxrBump",asUtility=True)
            cmds.connectAttr(filenode+".outColor",Displacement+".inputN")
            cmds.setAttr(Displacement+".scale",.4)
            cmds.connectAttr(Displacement+".resultN",NewMat+".bumpNormal",f=True)
    
        

def basicConvert(mat,To):

    try:
        fileNode = cmds.listConnections(mat+".color",d=True)[0]
    except:
        fileNode = cmds.listConnections(mat+".color",d=True)

    NewMat = createShader(MATERIALCOMMANDS.get(To))

    cmds.delete(cmds.listConnections(NewMat+".outColor",d=True)[0])
    convFromYtoX(mat,NewMat)
    connectDiffuse(fileNode,NewMat,mat)
    
    if cmds.checkBox("enableAlpha",q=True,v=True) == True:
        connectAlpha(fileNode,NewMat,mat)
    if cmds.checkBox("disableMipMap",q=True,v=True) == True:
        disableMipMaps(fileNode,NewMat)
    if cmds.checkBox("EnableExtra",q=True,v=True) == True:
        if To in str(CUSTOMBEHAVIOUR):
            connectSpecial(mat,NewMat,To)
        else:
            print("Render engine isnt in custom behaviour, Skipping.")
    
    cmds.delete(mat)
    cmds.rename(NewMat,mat+"_"+To)

def proxyConvert(mat,To):

    try:
        fileNode = cmds.listConnections(mat+".color",d=True)[0]
    except:
        fileNode = cmds.listConnections(mat+".color",d=True)

    NewMat = createShader(MATERIALCOMMANDS.get(To))

    cmds.setAttr(cmds.listConnections(NewMat+".outColor",d=True)[0] + ".ihi", 0)
    shadingE = cmds.listConnections(mat+".outColor",d=True)[0]
    cmds.connectAttr(NewMat+".outColor",shadingE+SHADINGNODE.get(cmds.nodeType(NewMat)))

    connectDiffuse(fileNode,NewMat,mat)
    if cmds.checkBox("enableAlpha",q=True,v=True) == True:
        connectAlpha(fileNode,NewMat,mat)
    if cmds.checkBox("disableMipMap",q=True,v=True) == True:
        disableMipMaps(fileNode,NewMat)
    if cmds.checkBox("EnableExtra",q=True,v=True) == True:
        if To in str(CUSTOMBEHAVIOUR):
            connectSpecial(mat,NewMat,To)
        else:
            print("Render engine isnt in custom behaviour, Skipping.")

    cmds.disconnectAttr(mat + ".msg", "defaultShaderList1.s", na=True)
    cmds.rename(NewMat,mat+"_"+To)    

def startConvert(From:str,To:str):
    try:
        if To in str(PLUGINLIST.items()):
            cmds.loadPlugin(PLUGINLIST.get(To))
    except Exception as f:
        print(f"Error happened while starting, Error: {f}")
        return

    allMats = getSelection(From)

    if allMats in EMPTY:
        print("No selected or valid objects!")
        return None

    for i in allMats:
        if cmds.checkBox("proxymode",q=True,v=True) == True:
            proxyConvert(i,To)
        else:
            basicConvert(i,To)

def start():
    startConvert(cmds.optionMenu("FromMat",q=True,v=True),cmds.optionMenu("ToMat",q=True,v=True))

#Run if ran directly
if __name__=="__main__":  
    deleteIfOpen()
    mayaWindow()