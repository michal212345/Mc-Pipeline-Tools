import maya.cmds as cmds
import maya.mel as mel

from PySide2.QtCore import *
from PySide2.QtGui import * 

###

# TO DO

# * Rewrite the wholething
# * Finish region selection

###

###
# VERSION CHECKS 
###

#Display the correct icon for different maya version

if cmds.about(version=True) <= "2022":
    BROSEIMAGE = "browseFolder.png"
    cmds.confirmDialog(title='Version warning', icon="information" , message="There are a few issues with this script running in Maya 2022, the script will run but with errors like unintended behaviour. For example buttons breaking, please be careful", button=['Ok'], defaultButton='Ok')
else:
    BROSEIMAGE = "folder-open.png"

###
# Image handler
###

class ImageData:

    """
    Handle image data.
    """

    def __init__(self,path):
        self.picture = QImage(path)
        self.Path2image = path

    def GetAlpha(self,X:int,Y:int):
        return self.picture.pixelColor(QPoint(X,Y)).__reduce__()[2][1][3]

    def GetResolution(self) -> list:
        size = []

        size.append(self.picture.height())
        size.append(self.picture.width())

        return size
    
    def getPath(self) -> str:
        return str(self.Path2image)

    def clear(self):
        self.picture = QImage(None)




def DelAlphaPixels(pathI):
    """
    Find, Select and deleted mesh faces with alpha inside of them
    """

    def uvfix(faces):

        """
        Fixes texture issue that happens when you extrude objects perfectly up
        
        faces(list(str)): Either takes Face list or entire meshes
        """
        
        cmds.progressWindow(title="MC UV",status="Uving " + str(faces),progress=0,ii=False)

        Mesh=faces
        MeshFace = cmds.polyListComponentConversion(Mesh,tf=True)
        MeshFace = cmds.filterExpand(MeshFace, sm=34)
        Div = len(MeshFace)
        f = 0
        delundo = 0
        cmds.polyMapCut(MeshFace,ch=True)
        for i1 in range(len(MeshFace)):
            MeshUv = cmds.polyListComponentConversion(MeshFace[i1],ff=True,tuv=True)
            MeshUv = cmds.filterExpand(MeshUv, sm=35)
            loca=[0,0]
            for i in range(len(MeshUv)):
                loc=cmds.polyEditUV(MeshUv[i],q=True,u=1,v=1)
                loca[0]=loca[0] + loc[0]
                loca[1]=loca[1] + loc[1]
            delundo = delundo + 1
            f = f + 1
            cmds.progressWindow(edit=True,progress=f/Div*100)
            loca[0]=loca[0] / 4
            loca[1]=loca[1] / 4
            cmds.polyEditUV(MeshFace[i1],pv=loca[1], sv=0.5, su=0.5, pu=loca[0])
            #Cleans undo to make sure the undos dont crash maya
            if delundo == 50:
                mel.eval("flushUndo;")
                delundo = 0
        
        cmds.progressWindow(ep=True)
        cmds.select(d=True)

    def optimizeEdges(Object:str,lowA:int,HighA:int):
        cmds.selectMode(object=True)
        cmds.select(cmds.polyListComponentConversion(Object,te=True))
        cmds.polySelectConstraint( m=3, t=0x8000, a=True, ab=(lowA, HighA) )
        HardEdges = cmds.ls(sl=True)
        cmds.polySelectConstraint(m=0, a=False)
        cmds.select(HardEdges)
        mel.eval("GrowLoopPolygonSelectionRegion;SelectEdgeLoopSp;InvertSelection;")
        cmds.polyDelEdge(cmds.ls(sl=True),cv=True)

    def CreatePlane(pathI):

        """
        Creates plane and texture corresponding.
        """
        global Image
        Resolution = Image.GetResolution()

        mel.eval("polyPlane -w 16 -h 16 -sx "+ str(Resolution[0]) + " -sy " + str(Resolution[1]) + " -ax 0 1 0 -cuv 2 -ch 1;")
        renamed = cmds.rename(cmds.ls(selection=True),"ExtrudedMesh#")

        mel.eval('hyperShadePanelCreate "shader" phong ;')
        matRenamed = cmds.rename(cmds.ls(selection=True),renamed+"Mat")
        cmds.select(renamed)
        mel.eval('hyperShade -assign '+str(matRenamed)+' ;')

        mel.eval('hyperShadePanelCreate "2dTexture" file;')
        cmds.rename(cmds.ls(selection=True),renamed+"Tex")
        cmds.setAttr(renamed+"Tex.fileTextureName", pathI, type="string")
        cmds.connectAttr(renamed+"Tex.outColor",matRenamed+".color")
        cmds.setAttr(renamed+"Tex.filterType", 0)

        return renamed

    def AlphaThreshHold(X:int,Y:int) -> bool:

        """
        Check if alpha is within fresh-hold and return bool
        """

        Alpha = Image.GetAlpha(X,Y)

        if Alpha <= cmds.floatSliderGrp("AThreshold",q=True,v=True):
            return True
        else:
            return False

    Resolution = Image.GetResolution()

    Mesh = str(CreatePlane(pathI))
    cmds.select(Mesh)

    faceC = 0
    toDel = []

    #Loop through the res of image, then add to array any alpha pixels to delete.
    for i in range(Resolution[0]):
        for b in range(Resolution[1]):
            if AlphaThreshHold(i,b) == True:
                toDel.append(Mesh+".f["+str(faceC)+"]")
                faceC = faceC + 1
            else:
                faceC = faceC + 1
                continue


    #Delete faces from the loop
    try:
        cmds.polyDelFacet(toDel)
    except:
        cmds.warning("No faces to delete.")
    cmds.select(Mesh)
    mel.eval("ConvertSelectionToEdgePerimeter;")

    Faceedges = cmds.ls(sl=True)
    
    MeshF = cmds.polyListComponentConversion(Mesh, tf=True)
    MeshF = cmds.filterExpand(MeshF, sm=34)

    #Rotate uv into correct oriantation, since image and mesh faces dont align
    cmds.select(MeshF)
    mel.eval("polyEditUV -pu 0.5 -pv 0.5 -a -90 -rr 1")
    cmds.select(Mesh)

    #Copy original uv before fix
    cmds.polyUVSet( copy=True, uvSet='map1' )

    #Fix Nonmanifold geometry by disconecting specific vertex/faces
    mel.eval('expandPolyGroupSelection; polyCleanupArgList 4 { "0","2","1","0","0","0","0","0","0","1e-05","0","1e-05","0","1e-05","0","1","0","0" };')
    mel.eval('DetachComponent;')



    # I cant be asked to split this into another function so here it is!
    # Remove alpha also handles all extrude! :)
    
    if cmds.checkBox("ToExtrude",q=True,v=True):
        MeshName = Mesh

        if cmds.checkBox("uvEdges",q=True,v=True):
            uvfix(Faceedges)
        else:
            uvfix(Mesh)

        try:
            Mesh = cmds.polySeparate(Mesh)
        except:
            cmds.warning("PNG2Mesh: Cant Seperate one mesh, Skipping.")
        finally:
            Mesh = cmds.filterExpand(Mesh,sm=12)

        cmds.select(d=True)

        #Handle extrude if there's one or multiple meshes
        if type(Mesh) == list:
            for i in Mesh:
                cmds.polyExtrudeFacet( i, kft=True, ltz=float(cmds.floatSliderGrp("ESize",q=True,v=True)) )
        elif type(Mesh) == str:
            cmds.polyExtrudeFacet( Mesh, kft=True, ltz=float(cmds.floatSliderGrp("ESize",q=True,v=True)) )
        else:
            cmds.warning("PNG2Mesh: Error in extrude.")
            return None

        try:
            if cmds.checkBox("OptimizeMesh",q=True,v=True):
                if type(Mesh) == list:
                    for i in Mesh:
                        cmds.select(MeshName)  
                        optimizeEdges(i,45,91)
                elif type(Mesh) == str:
                    optimizeEdges(Mesh,45,91)
                else:
                    cmds.warning("PNG2Mesh: Error in Optimize Mesh.")
                    return None
        except:
            cmds.warning("Optimized Skipped")
        #Handle Bevel if there's one or multiple meshes       
        if cmds.checkBox("BevelMesh",q=True,v=True):
            if type(Mesh) == list:
                MeshC = cmds.filterExpand(Mesh,sm=12)
                for i in MeshC:
                    cmds.polyBevel3(i,o=0.1,sg=2,fn=True,ws=True)
                    mel.eval("PolygonSoftenEdge;")
            elif type(Mesh) == str:
                cmds.polyBevel3(Mesh,o=0.1,sg=2,fn=True,ws=True)
                mel.eval("PolygonSoftenEdge;")
            else:
                cmds.warning("PNG2Mesh: Error in bevel.")
                return None


        try:
            Mesh = cmds.polyUnite(Mesh)
        except:
            None
        finally:
            cmds.select(Mesh)


        if cmds.checkBox("RecEdge",q=True,v=True):
            cmds.select(Mesh)
            mel.eval("PolyMerge;")
            cmds.select(d=True)

    if cmds.checkBox("DelHistory",q=True,v=True):
        cmds.select(Mesh)
        mel.eval("DeleteHistory;")

    try:
        cmds.rename(Mesh[0],MeshName)
    except:
        cmds.warning("PNG2Mesh: Couldent rename mesh back to original name.")

    mel.eval("flushUndo;")
    cmds.select(d=True)

def Ext_start():
    """
    Handles start, fixes occasinal bug with the class not updating and extuding the previouse mesh.
    """
    
    def reutrnfilename(i:str):
        paths = i.split("/")
        return paths[-1]

    filelist = str(cmds.textField("PngFile",q=True,tx=True)).split(" | ")

    for i in filelist:
        global Image
        Image = ImageData(i)
        resolution = Image.GetResolution()

        if resolution[0] == resolution[1] and not resolution[0] == 0:
            DelAlphaPixels(i)
        else:
            cmds.confirmDialog( title='Invalid',icn="warning", message='The image needs to be a Square', button='Okay', dismissString='Okay' )
            Image.clear()
            cmds.error(f"The image {reutrnfilename(i)} is not a square")

###############
## UI CODING ##
###############

WINDOW_TITLE = "PNG Mesh creator"
WINDOW_WIDTH = 500

ROW_SPACING = 1
PADDING = 3

# Parts of UI Elements by Trainguy, modified and adjusted to what i need.

# Utility methods

def addColumnLayout():
    cmds.columnLayout(adjustableColumn=True, columnAttach=('both', PADDING))
    
def addFrameColumnLayout(identifier,label, collapsable,hidden=True):
    cmds.frameLayout(identifier,collapsable=collapsable, label=label,vis=hidden)
    addColumnLayout()

def parentToLayout():
    cmds.setParent('..')

def addSpacer():
    cmds.columnLayout(adjustableColumn=True)
    cmds.separator(height=PADDING, style="none")
    parentToLayout()
    
def addHeader(windowTitle):
    addColumnLayout()
    cmds.text(label='<span style=\"color:#ccc;text-decoration:none;font-size:20px;font-family:courier new;font-weight:bold;\">' + windowTitle + '</span>', height=50)
    parentToLayout()
    
def addText(label):
    return cmds.text(label=label)

def addCheckbox(identifier, label,cc = None, value=False,editable=True):
    cmds.checkBox(identifier,label=str(label),cc=str(cc),v=bool(value),ed=bool(editable))

def addButton(label, command, identifier,visable=True):
    addColumnLayout()
    cmds.separator(height=ROW_SPACING, style="none")
    controlButton = cmds.button(identifier, label=label, command=(command),vis=visable)
    cmds.separator(height=ROW_SPACING, style="none")
    return controlButton
                 
def deleteIfOpen():  
    if cmds.window('windowObject', exists=True):
        cmds.deleteUI('windowObject')
        
def getCloseCommand() -> str:
    return('cmds.deleteUI(\"' + 'windowObject' + '\", window=True)')

def addOptionMenu(identifier:str,label:str,menuitems=["1","2","3"],cc=None):
    cmds.optionMenu(identifier, label=str(label),cc=str(cc))
    for i in menuitems:
        cmds.menuItem(label=str(i))
        
# Int Slider
def addIntSliderGroup(identifier,min:int, max:int, value:int):
    return cmds.intSliderGrp(identifier,field=True, minValue=min, maxValue=max, fieldMinValue=min, fieldMaxValue=max, value=value)
          
# Float Slider
def addFloatSliderGroup(identifier,min:float, max:float, value:float):
    return cmds.floatSliderGrp(identifier,field=True, minValue=min, maxValue=max, fieldMinValue=min, fieldMaxValue=max, value=value)

# File Browser

# 0     Any file, whether it exists or not.
# 1     A single existing file.
# 2     The name of a directory. Both directories and files are displayed in the dialog.
# 3     The name of a directory. Only directories are displayed in the dialog.
# 4     Then names of one or more existing files.

def browseForDirectory(identifier,mode:int,Filtertype:str):

    if not cmds.checkBox('multiple', q=True, v=True):
        path = cmds.fileDialog2(fileMode=mode,fileFilter= Filtertype)
    else:
        path = cmds.fileDialog2(fileMode=4, fileFilter= Filtertype)

    combined = " | ".join(path)
    
    try:
        cmds.textField(identifier, edit=True,editable=True, text=str(combined))
    except:
        None
    finally:
        cmds.textField(identifier, edit=True,editable=False)

        cmds.frameLayout("ImageSettings",edit=True,vis=True,cl=True)
        cmds.button("Startbutton",e=True,vis=True)
        cmds.frameLayout("ExtrudsionSet",edit=True,vis=True,cl=True)
        cmds.frameLayout("ExtraFeatures",edit=True,vis=True,cl=True)
    

def addFileBrowser(identifier, mode, placeholderText, defaultText,filetype="All Files (*.*)"):
    cmds.rowLayout(numberOfColumns=2, columnAttach=[(1, 'left', 0), (2, 'right', 0)], adjustableColumn=1, height=22)
    textFieldControl = cmds.textField(identifier,editable=False, placeholderText=placeholderText, text=defaultText)
    command = 'browseForDirectory("'+identifier+'", '+str(mode)+', "' + str(filetype) +'")'
    cmds.iconTextButton(identifier, style='iconOnly', image1=BROSEIMAGE, label='spotlight', command=command)
    cmds.setParent("..")
    return textFieldControl

def createWindow():
    cmds.window(
        'windowObject', 
        title=WINDOW_TITLE, 
        width=WINDOW_WIDTH,
        height=100,
        maximizeButton=False,
        resizeToFitChildren=True
    )
    
    addSpacer()
    addHeader('PNG2Mesh')
    addSpacer()

    cmds.rowLayout(
        numberOfColumns=3, 
        adjustableColumn3=3, 
        columnWidth3=[120, 50, 50],
        columnAlign3=['right', 'left', 'left'], 
        columnAttach3=['right', 'left', 'left']
    )

    cmds.checkBox('multiple', l='Multiple,')
    addText('Path:')
    addFileBrowser('PngFile', 1, 'Texture to extrude', '', "PNG File(*.png)")
    parentToLayout()
    parentToLayout()

    addFrameColumnLayout("ImageSettings","Image settings",True,False)
    cmds.gridLayout( numberOfColumns=2, cellWidthHeight=(300, 20) )
    addText("Alpha Threshold")
    addFloatSliderGroup("AThreshold",0,1,0.9) 
    parentToLayout()
    parentToLayout()
    parentToLayout()
    parentToLayout()

    addFrameColumnLayout("ExtrudsionSet","Extrusion settings",True,False)
    cmds.gridLayout( numberOfColumns=2, cellWidthHeight=(300, 20) )
    addCheckbox("ToExtrude","Extrude Mesh",value=True)
    addCheckbox("uvEdges","Uv only edges",value=False)
    addText("Extude size")
    addFloatSliderGroup("ESize",0,2,1)
    parentToLayout()
    parentToLayout()
    parentToLayout()
    parentToLayout()    

    addFrameColumnLayout("ExtraFeatures","Extra Features",True,False)
    cmds.gridLayout( numberOfColumns=2, cellWidthHeight=(300, 20) )
    addCheckbox("BevelMesh","Bevel Mesh",value=False,cc="blockCkeckBoxUI(['BevelMesh',],'RecEdge')")
    addCheckbox("DelHistory","Delete History",value=True)
    addCheckbox("OptimizeMesh","Optimize Mesh",value=True)
    addCheckbox("RecEdge","Reconnect Vertex",value=False,cc="blockCkeckBoxUI(['RecEdge'],'BevelMesh')")
    parentToLayout()
    parentToLayout()
    parentToLayout()
    parentToLayout()
    parentToLayout()
    parentToLayout()

    addButton("Start","Ext_start();cmds.modelEditor('modelPanel4', edit=True, dtx=1)","Startbutton",False)
    parentToLayout()
    addButton("Close",getCloseCommand(),"Closebutton")
    parentToLayout()
    parentToLayout()
    

    cmds.showWindow('windowObject')  

def blockCkeckBoxUI(FromIdf:list,toBlockIdf,reverse=False):

    """
    Handles blocking checkbox buttons
    """

    checkbox = False

    for i in FromIdf:
        if bool(cmds.checkBox(i,q=True,v=True)) == True:
            checkbox = True
        else:
            continue

    if reverse == False:
        if checkbox == True:
            cmds.checkBox(toBlockIdf,edit=True,v=False,ed=False)
        elif checkbox == False:
            cmds.checkBox(toBlockIdf,edit=True,ed=True)
    else:
        if checkbox == True:
            cmds.checkBox(toBlockIdf,edit=True,ed=True)
        elif checkbox == False:
            cmds.checkBox(toBlockIdf,edit=True,v=False,ed=False)        

#Run if ran directly
if __name__=="__main__":  
    deleteIfOpen()
    createWindow()
