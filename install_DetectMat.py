import maya.cmds as cmds

buttonscript = r'''
import maya.cmds as cmds
import maya.mel as mel
import os    

def main(SpecularSuffix,NormalSuffix,AOSuffix,mipmaps,workspace):

    def check_containing(find,listof):

        """Search for texture named (find) inside of (listof) paths
            If... There are two files named the same in seperate folders, let the user pick which one.
            
        Returns:
            str: Path to choosen file
        """
        
        match = []
        
        #Check all paths for exact filename given in (find) from (listof)
        n = 0
        for i in listof:
            i = i.split("\\")
            if i[-1] == find:
                match.append(listof[n])
            n = n + 1
        
        #If no objects found error checking...
        if len(match) == 0:
            print("Len 0 error")
            return ""
        
        #If object in match does not exist error checking...
        elif len(match) == 1:
            if not os.path.exists(match[0]):
                print("Len file doesnt exist error")
                return ""
            return str(match[0])
        
        #If multiple files named the same, give the user a choise...
        else:
            n = 0
            print("Material: ",find)
            for i in match:
                if not os.path.exists(i):
                    print("List file doesnt exist error")
                    return ""
                print(n,i)
                n = n + 1

            numberoffiles = range(len(match))
            print("\n")
            
            #Super unconventional way of using confirmdialog and i love it <3
            return match[int(cmds.confirmDialog(title="Please choose a path",m="check log for more detail",b=numberoffiles,db="0"))]

    def setSecondUv(mat,filenode):
        uvChooser = cmds.shadingNode("uvChooser",asUtility=True)
        placeTexture = cmds.listConnections(filenode+".mirrorU",c=True)[1]
        cmds.connectAttr(uvChooser+".outUv",placeTexture+".uvCoord")
        shadingEngine = cmds.listConnections(mat+".outColor",c=True)[1]
        mesh = cmds.listConnections(shadingEngine+".dagSetMembers",c=True)[1]
        try:
            cmds.connectAttr(mesh+"uvSet[1].uvSetName",uvChooser+"uvSets[0]")
        except:
            None

    listoffiles=[]

    # Get workspace, Extract all paths/files inside sourceimages and combine them into list.
    #workspace:str = cmds.workspace(fn=True)+"\sourceimages"
    for root, _, files in os.walk(workspace, topdown=False):
       for name in files:
          listoffiles.append(str(os.path.join(root, name).replace("/","\\")))

    #Run/Check specular
    combinedlist = '\t'.join(listoffiles)

    if len(cmds.ls(sl=True)) == 0:
        cmds.warning("Zero objects in selection")
        return
    #Grab selection nodetype
    nodetype = cmds.objectType(cmds.ls(sl=True,tl=1))

    #Check node type and return Material
    if not nodetype == "phong":
        if nodetype == "mesh" or nodetype == "transform":
            theNodes = cmds.ls(sl = True, dag = True, s = True)
            shadeEng = cmds.listConnections(theNodes , type = "shadingEngine")
            selection = cmds.ls(cmds.listConnections(shadeEng ), materials = True)
        else:
            #If not supported node type isnt found... Just error out :D
            print("Current selection is not supported.")
            return
    else:
        selection = cmds.ls(sl=True, type="phong")

    for mat in selection:

        # Check if there's a file connected
        listConnection:list[str] = cmds.listConnections(mat+".color",c=True)
        listConnection.remove(mat+".color")

        if len(listConnection) == 0:
            continue
        
        #If not empty, get the filepath of the texture
        matfile:str = cmds.getAttr(listConnection[0]+".fileTextureName")

        #Split it to extract the texture name
        matfilename = matfile.split("/")[-1]
        matfilename = matfilename.split(".")[0]

        if cmds.attributeQuery("reflectivity",node=mat,ex=True):
            if matfilename+SpecularSuffix+".png" in combinedlist:

                temp = check_containing(matfilename+SpecularSuffix+".png",listoffiles)

                filenode = mel.eval('hyperShadePanelCreate "2dTexture" file;')

                #Setup, adjust and connect the _spec to Reflection weight
                cmds.setAttr(filenode+".fileTextureName",str(temp),type="string")
                cmds.setAttr(filenode+".colorSpace","Raw",type="string")

                if mipmaps == True:
                    cmds.setAttr(filenode+".filterType",0)
                    #cmds.setAttr(filenode+".rsFilterEnable",0)

                try:
                    cmds.connectAttr(filenode+".outColorR",mat+".reflectivity")
                except:
                    cmds.delete(filenode)
                    print("Couldnt connect to: "+ mat+".reflectivity")
        else:
            print(f"Material {mat} does not contain reflectivity attribute! For this to work the material must be a phong!")

        #Run/Check Normals
        if matfilename+NormalSuffix+".png" in combinedlist:
            
            temp = check_containing(matfilename+NormalSuffix+".png", listoffiles)
            
            filenode = mel.eval('hyperShadePanelCreate "2dTexture" file;')
            
            #Setup and adjut the _Normals filenode.
            cmds.setAttr(filenode+".fileTextureName",str(temp),type="string")
            cmds.setAttr(filenode+".colorSpace","Raw",type="string")
            
            setSecondUv(mat,filenode)

            #if connection exists... skip delete created files
            #I could probably re write the script to do it first but cba :joy:
            try:
                cmds.connectAttr(filenode+".outColor",mat+".normalCamera")
            except:
                cmds.delete(filenode)
                print("Couldnt connect to: "+mat+".normalCamera")
        
        #Run/Check AO        
        if matfilename+AOSuffix+".png" in combinedlist:

            temp = check_containing(matfilename+AOSuffix+".png", listoffiles)
            
            filenode = mel.eval('hyperShadePanelCreate "2dTexture" file;')
            
            #Setup and adjut the _Normals filenode.
            cmds.setAttr(filenode+".fileTextureName",str(temp),type="string")
            
            setSecondUv(mat,filenode)
            
            try:
                cmds.connectAttr(filenode+".outColor",mat+".ambientColor")
            except:
                cmds.delete(filenode)
                print("Couldnt connect to: "+mat+".ambientColor")        

def browseForDirectory(identifier, mode,Filtertype):
    path = cmds.fileDialog2(fileMode=int(mode),fileFilter= str(Filtertype))
    try:
        cmds.textField(identifier, edit=True, text=path[0])
    except:
        None

def addFileBrowser(identifier, mode, placeholderText, defaultText,filetype="All Files (*.*)"):
    cmds.rowLayout(numberOfColumns=2, columnAttach=[(1, 'left', 0), (2, 'right', 0)], adjustableColumn=1, height=22)
    textFieldControl = cmds.textField(identifier, placeholderText=placeholderText, text=defaultText)
    cmds.iconTextButton(identifier, style='iconOnly', image1='browseFolder.png', label='spotlight', command='browseForDirectory("'+identifier+'", '+str(mode)+', "' + str(filetype) +'")')
    cmds.setParent("..")
    return textFieldControl;

def deleteIfOpen():  
    if cmds.window('Spec_Normal', exists=True):
        cmds.deleteUI('Spec_Normal')
                
def mayaWindow():
    ## Ui code...
    #Let user define the suffix of Spec and normal
    cmds.window('Spec_Normal', title="Test", width=200, height=200, maximizeButton=False, resizeToFitChildren=True)
    cmds.columnLayout(adjustableColumn=True)
    
    cmds.rowLayout(numberOfColumns=2, adjustableColumn2=2, columnWidth2=[120, 50],columnAlign2=['right', 'left'], columnAttach2=['right', 'left'])
    cmds.text("Material directories:")
    addFileBrowser('MaterialFolder', 2, 'Export Directory', '',"Folder")
    cmds.setParent('..')
    cmds.setParent('..')
    
    cmds.rowLayout(numberOfColumns=2, adjustableColumn2=2, columnWidth2=[120, 50],columnAlign2=['right', 'left'], columnAttach2=['right', 'left'])
    cmds.text("Specular Suffix:")
    cmds.textField("Spec",tx="_Spec")
    cmds.setParent('..')
    cmds.setParent('..')
    
    cmds.rowLayout(numberOfColumns=2, adjustableColumn2=2, columnWidth2=[120, 50],columnAlign2=['right', 'left'], columnAttach2=['right', 'left'])
    cmds.text("Normal Suffix:")
    cmds.textField("Normal",tx="_Normal")
    cmds.setParent('..')
    cmds.setParent('..')

    cmds.rowLayout(numberOfColumns=2, adjustableColumn2=2, columnWidth2=[120, 50],columnAlign2=['right', 'left'], columnAttach2=['right', 'left'])
    cmds.text("AO Suffix:")
    cmds.textField("AO",tx="_AO")
    cmds.setParent('..')
    cmds.setParent('..')

    cmds.rowLayout(numberOfColumns=2, adjustableColumn2=2, columnWidth2=[120, 50],columnAlign2=['right', 'left'], columnAttach2=['right', 'left']) 
    cmds.checkBox("Mipmap",l="Disable mipmaps?")
    cmds.button(l="Start",c="run()")
    cmds.setParent('..')
    cmds.setParent('..')
    
    cmds.showWindow('Spec_Normal')


def run():
    if cmds.textField("MaterialFolder", q=True, tx=True) == "":
        cmds.error("No path given to work with.")
        return
    else:
        main(str(cmds.textField("Spec",q=True,tx=True)),str(cmds.textField("Normal",q=True,tx=True)),str(cmds.textField("AO",q=True,tx=True)),bool(cmds.checkBox("Mipmap",q=True,v=True)),str(cmds.textField("MaterialFolder", q=True, tx=True)))
        deleteIfOpen()

#Run if ran directly
if __name__=="__main__":  
    deleteIfOpen()
    mayaWindow()
'''


    
def onMayaDroppedPythonFile(*args):

    ICON = "eblinn.svg"
    LNAME = "Detect materials for material"

    import maya.mel as mel

    topShelf = mel.eval('$nul = $gShelfTopLevel')
    currentShelf = cmds.tabLayout(topShelf, q=1, st=1)
    cmds.shelfButton(parent=currentShelf, c=buttonscript, label=LNAME, i=ICON)
