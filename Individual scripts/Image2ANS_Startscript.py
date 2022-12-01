import multiprocessing as mp
import maya.cmds as cmds
import os, time
def browseForDirectory(identifier:str, mode:int):
    ########
    def get_material_file(mat_node:list):
        """Get the file path of the currently selected material node.

        Args:
            mat_node (list): List of materials

        Returns:
            String: The path inside main color of material.
        """
        
        material_list=["aiStandardSurface","phongE","RedshiftMaterial","blinn","phong","lambert"]
        material_solver ={
            "RedshiftMaterial":".diffuse_color",
            "aiStandardSurface":".baseColor"}
        
        if len(mat_node) == 0:
            cmds.error("You have not selected any materials.")
        
        elif len(mat_node) == 1:
            mat_node = mat_node[0]
        
        if type(mat_node) == list:
            temp =[]
            for i in mat_node:
                material_type = cmds.nodeType(i)
                if material_type in str(material_list):
                    if material_type in str(material_solver.items()):
                        file_node = cmds.listConnections(i+material_solver.get(material_type),d=True)
                    else:
                        file_node = cmds.listConnections(i+".color",d=True)
                    print(str(cmds.getAttr(file_node[0]+".fileTextureName")))
                    temp.append(str(cmds.getAttr(file_node[0]+".fileTextureName")))
                else:
                    cmds.error(str(i)+" is not a material.")
            return temp
        else:
            material_type = cmds.nodeType(mat_node)
            if material_type in str(material_list):
                if material_type in str(material_solver.items()):
                    file_node = cmds.listConnections(mat_node+material_solver.get(material_type),d=True)
                else:
                    file_node = cmds.listConnections(mat_node+".color",d=True)
                print(str(cmds.getAttr(file_node[0]+".fileTextureName")))
                return str(cmds.getAttr(file_node[0]+".fileTextureName"))
            else:
                cmds.error(str(material_list)+" is not a material.")
    
    ##########
    
    #Grab current option and run code based on option
    state = cmds.optionMenu("process", q=True, v=True)
    
    if state == "Folder":
        path = cmds.fileDialog2(fileMode = 2, fileFilter="Folder")
    elif state == "Single Image":
        path = cmds.fileDialog2(fileMode = 1, fileFilter="PNG (*.PNG)")
    elif state == "Material":
        path = get_material_file(cmds.ls(sl=True))
    else:
        print("Haha funny error moment")
    
    try:
        cmds.textField(identifier, edit=True, text=path)
    except:
        cmds.textField(identifier, edit=True, text=path[0])

def addFileBrowser(identifier, mode, placeholderText, defaultText,filetype="All Files (*.*)"):
    cmds.rowLayout(numberOfColumns=2, columnAttach=[(1, 'left', 0), (2, 'right', 0)], adjustableColumn=1, height=22)
    textFieldControl = cmds.textField(identifier, placeholderText=placeholderText, text=defaultText)
    cmds.iconTextButton(identifier, style='iconOnly', image1='browseFolder.png', label='spotlight', command='browseForDirectory("'+identifier+'", '+str(mode)+')')
    cmds.setParent("..")
    return textFieldControl;

def addDropDown(identifier,label,items,cc="None"):
    cmds.optionMenu(identifier,label=label,cc=cc)
    for i in items:
        cmds.menuItem(label = i)

def update_Numb(intId,txId):
    cmds.text(txId,edit=True,l=str(cmds.intSlider(intId,q=True,v=True)))

def single_core_warn(id):
    if not bool(cmds.checkBox(id,q=True,v=True)):
        result = cmds.confirmDialog(t="Warning",m="Single core can be painfully slow, Are you sure?" ,icn="critical" ,button=["Yes","No"])
        if result == "No":
            cmds.checkBox(id,edit=True,v=True)

def deleteIfOpen():  
    if cmds.window('Image2ans', exists=True):
        cmds.deleteUI('Image2ans')

def mayaWindow():
    #Let user define the suffix of Spec and normal
    cmds.window('Image2ans', title="Image to ANS", width=300, height=200, maximizeButton=False, resizeToFitChildren=True)
    cmds.columnLayout(adjustableColumn=True)
    cmds.rowLayout(numberOfColumns=3, adjustableColumn3=3, columnWidth3=[120, 70, 120],columnAlign3=['left', 'left', 'left'], columnAttach3=['left', 'left', 'left'])
    cmds.checkBox('AOCb',l='Ambient Occlusion',v=True)
    cmds.checkBox('SpecCb',l='Specular',v=True)
    cmds.checkBox('NormalCb',l='Normals',v=True)
    cmds.setParent('..')
    cmds.setParent('..')
    cmds.setParent('..')

    cmds.rowLayout(numberOfColumns=2, adjustableColumn2=2, columnWidth2=[160, 120],columnAlign2=['right', 'left'], columnAttach2=['right', 'left'])
    addDropDown('process',"Process:",["Folder","Single Image","Material"],'cmds.textField("MaterialFolder",edit=True,text="")')
    cmds.checkBox('SinOrMulti',l="MultiCore ", v=True, cc='single_core_warn("SinOrMulti")')
    cmds.setParent('..')
    cmds.setParent('..')    
    
    cmds.rowLayout(numberOfColumns=3, adjustableColumn3=3, columnWidth3=[120, 120, 120],columnAlign3=['left', 'left', 'left'], columnAttach3=['left', 'left', 'left'])
    cmds.text(label="smoothness setting:")
    cmds.intSlider('smInt', min=1, max=10, value=5,cc='update_Numb("smInt","smNr")' )
    cmds.text('smNr',l=5)
    cmds.setParent('..')
    cmds.setParent('..')
    cmds.setParent('..')
    cmds.rowLayout(numberOfColumns=3, adjustableColumn3=3, columnWidth3=[120, 120, 120],columnAlign3=['left', 'left', 'left'], columnAttach3=['left', 'left', 'left'])
    cmds.text(label="strength setting:")
    cmds.intSlider('stInt', min=1, max=10, value=5, cc='update_Numb("stInt","stNr")')
    cmds.text('stNr',l=5)
    cmds.setParent('..')    
    cmds.setParent('..')
    cmds.setParent('..')
    
    cmds.rowLayout(numberOfColumns=2, adjustableColumn2=2, columnWidth2=[120, 50],columnAlign2=['right', 'left'], columnAttach2=['right', 'left'])
    cmds.text("Material directories:")
    addFileBrowser('MaterialFolder', 2, 'Export Directory', '',"Folder")
    cmds.setParent('..')
    cmds.setParent('..')
    
    cmds.rowLayout(numberOfColumns=2, adjustableColumn2=2, columnWidth2=[120, 50],columnAlign2=['right', 'left'], columnAttach2=['right', 'left']) 
    cmds.separator(height=12, style="none")
    cmds.button(l="Start",c="Start_ANS()")
    cmds.setParent('..')
    cmds.setParent('..')
    cmds.showWindow('Image2ans')

def Start_ANS():
    def remove_Filename(path:str) -> str:
        """Remove the filename from path

        Args:
            path (str): The path string

        Returns:
            String: Path with no filename in it.
        """
        paths = path.split("\\")
        paths.pop(len(paths)-1)
        path = "\\".join(paths)
        
        return path
    
    def splitx(list_a:list, chunk_size:int) -> list:
        """Split list into defined chunks, list_a divided by chunk_size

        Args:
            list_a (str): Full list of objects
            chunk_size (int): Number to divide the list_a into

        Returns:
            List(list(str)): A list with smaller list
        """
        
        temp=[]
        for i in range(0, len(list_a), chunk_size):
            temp.append(list_a[i:i + chunk_size])
        return temp    
    
    # Check if core is in script folder.
    try:
        import Image2ANS as ANS
    except:
        cmds.confirmDialog(t="Warning",m="The script has not detected Image2ANS!" ,icn="critical" ,button="Ok")
        return
    

    input_file=[]
    path = str(cmds.textField("MaterialFolder",q=True,tx=True))
    path = path.replace("/","\\")
    
    if not os.path.exists(path):
        cmds.error("The file does not exist " + str(path))
    
    if cmds.optionMenu("process", q=True, v=True) == "Folder":

        for root, _, files in os.walk(path, topdown=False):
            for name in files:
                    if os.path.exists(os.path.join(root, name).replace("/","\\")):
                        input_file.append(os.path.join(root, name).replace("/","\\"))
        
        for b in input_file:
            for i in ["Ao","Normal","Spec","Resized"]:
                final_path = os.path.join(remove_Filename(b),i)
                if not os.path.isdir(final_path):
                    os.makedirs(final_path)
    
    elif cmds.optionMenu("process", q=True, v=True) == "Single Image" or cmds.optionMenu("process", q=True, v=True) == "Material":
        #Variable fix for later code
        if type(path) == list:
            for i in path:
                input_file.append(i)
        elif type(path) == str:
            input_file.append(path)
        
        path = remove_Filename(path)
        #Generate folders for output.
        for i in ["Ao","Normal","Spec","Resized"]: 
            final_path = os.path.join(path,i)
            if not os.path.isdir(final_path):
                os.makedirs(final_path)
    
    #Setup vars
    smint = int(cmds.intSlider('smInt', q=True ,value=True))
    stint = int(cmds.intSlider('stInt', q=True,value=True))
    aocb = bool(cmds.checkBox('AOCb', q=True, v=True))
    speccb = bool(cmds.checkBox('SpecCb', q=True , v=True))
    normcb = bool(cmds.checkBox('NormalCb', q=True, v=True))
    
    #Check for multi or single core
    if cmds.checkBox('SinOrMulti', q=True, v=True):
        
        #Divide the task list by amount of cpu
        chunks = splitx(input_file,mp.cpu_count())
        
        #Set up multiprocessing
        ctx = mp.get_context("spawn")
        ctx.set_executable(os.environ["MAYA_LOCATION"]+"/bin/mayapy.exe")
        
        #Run multiprocessing
        p = []
        for i in chunks:
            for b in i:
                p.append(ctx.Process(target=ANS.Convert, args=(b, smint, stint, aocb, speccb, normcb,)))
            for pr in p:
                pr.start()
            for pr in p:
                pr.join()
            p.clear()
    else:
        #Single core cycle
        start = time.time()
        for i in input_file:
            ANS.Convert(i, smint, stint, aocb, speccb, normcb)
        end = time.time()
        print(f"Script took {end - start} seconds")
        
    #Try to remove the resized folder
    try:
        os.remove(os.path.join(path,"Resized"))
    except:
        None
    
#Run if ran directly
if __name__=="__main__":  
    deleteIfOpen()
    mayaWindow()