import os, maya.cmds as cmds

script=r"""import math, functools
import numpy as np
from scipy import ndimage
from matplotlib import pyplot
from PIL import Image, ImageOps,ImageEnhance
import os

def memoize(func):
    cache = {}    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        key = str(args) + str(kwargs)
        
        if key not in cache:
            cache[key] = func(*args, **kwargs)
        
        return cache[key]

    return wrapper

def smooth_gaussian(im:np.ndarray, sigma) -> np.ndarray:

    if sigma == 0:
        return im

    im_smooth = im.astype(float)
    kernel_x = np.arange(-3*sigma,3*sigma+1).astype(float)
    kernel_x = np.exp((-(kernel_x**2))/(2*(sigma**2)))

    im_smooth = ndimage.convolve(im_smooth, kernel_x[np.newaxis])

    im_smooth = ndimage.convolve(im_smooth, kernel_x[np.newaxis].T)

    return im_smooth

def gradient(im_smooth:np.ndarray):

    gradient_x = im_smooth.astype(float)
    gradient_y = im_smooth.astype(float)

    kernel = np.arange(-1,2).astype(float)
    kernel = - kernel / 2

    gradient_x = ndimage.convolve(gradient_x, kernel[np.newaxis])
    gradient_y = ndimage.convolve(gradient_y, kernel[np.newaxis].T)

    return gradient_x,gradient_y


def sobel(im_smooth):
    gradient_x = im_smooth.astype(float)
    gradient_y = im_smooth.astype(float)

    kernel = np.array([[-1,0,1],[-2,0,2],[-1,0,1]])

    gradient_x = ndimage.convolve(gradient_x, kernel)
    gradient_y = ndimage.convolve(gradient_y, kernel.T)

    return gradient_x,gradient_y


def compute_normal_map(gradient_x:np.ndarray, gradient_y:np.ndarray, intensity=1):

    width = gradient_x.shape[1]
    height = gradient_x.shape[0]
    max_x = np.max(gradient_x)
    max_y = np.max(gradient_y)

    max_value = max_x

    if max_y > max_x:
        max_value = max_y

    normal_map = np.zeros((height, width, 3), dtype=np.float32)

    intensity = 1 / intensity

    strength = max_value / (max_value * intensity)

    normal_map[..., 0] = gradient_x / max_value
    normal_map[..., 1] = gradient_y / max_value
    normal_map[..., 2] = 1 / strength

    norm = np.sqrt(np.power(normal_map[..., 0], 2) + np.power(normal_map[..., 1], 2) + np.power(normal_map[..., 2], 2))

    normal_map[..., 0] /= norm
    normal_map[..., 1] /= norm
    normal_map[..., 2] /= norm

    normal_map *= 0.5
    normal_map += 0.5

    return normal_map

#@memoize
def normalized(a) -> float: 
    factor = 1.0/math.sqrt(np.sum(a*a)) # normalize
    return a*factor

def my_gauss(im:np.ndarray):
    return ndimage.uniform_filter(im.astype(float),size=20)

def shadow(im:np.ndarray):
    
    shadowStrength = .5
    
    im1 = im.astype(float)
    im0 = im1.copy()
    im00 = im1.copy()
    im000 = im1.copy()

    for _ in range(0,2):
        im00 = my_gauss(im00)

    for _ in range(0,16):
        im0 = my_gauss(im0)

    for _ in range(0,32):
        im1 = my_gauss(im1)

    im000=normalized(im000)
    im00=normalized(im00)
    im0=normalized(im0)
    im1=normalized(im1)
    im00=normalized(im00)

    shadow=im00*2.0+im000-im1*2.0-im0 
    shadow=normalized(shadow)
    mean = np.mean(shadow)
    rmse = np.sqrt(np.mean((shadow-mean)**2))*(1/shadowStrength)
    shadow = np.clip(shadow, mean-rmse*2.0,mean+rmse*0.5)

    return shadow

def flipgreen(path:str):
    try:
        with Image.open(path) as img:
            red, green, blue, alpha= img.split()
            image = Image.merge("RGB",(red,ImageOps.invert(green),blue))
            image.save(path)
    except ValueError:
        with Image.open(path) as img:
            red, green, blue = img.split()
            image = Image.merge("RGB",(red,ImageOps.invert(green),blue))
            image.save(path)

def CleanupAO(path:str):
    try:
        with Image.open(path) as img:
            red, green, blue, alpha= img.split()
            NewG = ImageOps.colorize(green,black=(100, 100, 100),white=(255,255,255),blackpoint=0,whitepoint=180)
            NewG.save(path)
    except ValueError:
        with Image.open(path) as img:
            red, green, blue = img.split()
            NewG = ImageOps.colorize(green,black=(100, 100, 100),white=(255,255,255),blackpoint=0,whitepoint=180)
            NewG.save(path)

def adjustPath(Org_Path:str,addto:str):

    '''
    Adjust the given path to correctly save the new file.
    '''

    path = Org_Path.split("\\")
    file = path[-1]
    filename = file.split(".")[0]
    fileext = file.split(".")[-1]

    newfilename = addto+"\\"+filename + "_" + addto + "." + fileext
    path.pop(-1)
    path.append(newfilename)

    newpath = '\\'.join(path)

    return newpath

def Convert(input_file, smoothness = 5, intensity = 5, dAO = True, doS = True, doN = True):
    print('Doing: ',str(input_file))
    
    #maya.standalone.initialize(name='python')
    with Image.open(input_file,"r") as img:
        
        if doS == True:
            saturation = ImageEnhance.Color(img)

            saturation = saturation.enhance(0)
            brightnesscorect = ImageEnhance.Brightness(saturation)
            im_out = brightnesscorect.enhance(.75)
            im_out.save(adjustPath(input_file,"Spec"))
            print("Specular Done.")
        
        size = img.size
        sizen = list(size)
        if sizen[0] <= 2048 and sizen[1] <= 2048:
            while sizen[0] <= 2047 and sizen[1] <= 2047:
                sizen[0] = sizen[0] * 2
                sizen[1] = sizen[1] * 2
            
            resized = img.resize((sizen[0],sizen[1]),Image.Resampling.NEAREST)
            temp_file = adjustPath(input_file,"Resized")
            resized.save(temp_file)
            oldpath = input_file
            input_file = temp_file
            resized = True
        else:
            oldpath = input_file
            input_file = input_file

    if doN == True:
        im = pyplot.imread(input_file)

        if im.ndim == 3:
            im_grey = np.zeros((im.shape[0],im.shape[1])).astype(float)
            im_grey = (im[...,0] * 0.3 + im[...,1] * 0.6 + im[...,2] * 0.1)
            im = im_grey

        im_smooth = smooth_gaussian(im, smoothness)

        sobel_x, sobel_y = sobel(im_smooth)

        normal_map = compute_normal_map(sobel_x, sobel_y, intensity)

        pyplot.imsave(adjustPath(oldpath,"Normal"),normal_map)

        flipgreen(adjustPath(oldpath,"Normal"))
        print("Normal Done.")

    if dAO == True:
        im_shadow = shadow(im)

        pyplot.imsave(adjustPath(oldpath,"AO"),im_shadow)
        CleanupAO(adjustPath(oldpath,"AO"))
        print("Ambient Occlusion Done.")

    if resized == True:
        os.remove(temp_file)
        
    print("Done: ", input_file)
"""

buttonscript = r'''
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
    cmds.showWindow('Spec_Normal')

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
        import Image2ANS_Cuda as ANS
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
'''


    
def onMayaDroppedPythonFile(*args):

    def getscriptpath() -> str:

        '''
        Gets script path, puts the logs folder at the end.
        '''

        scriptPath = os.environ['MAYA_SCRIPT_PATH']

        ArrPath = scriptPath.split(";")

        #Rerive the maya scripts folder path from Maya
        ScrPath = [match for match in ArrPath if "Documents/maya/scripts" in match].__str__().translate({ord(i):None for i in "[]'"})

        return ScrPath

    try:
        import numpy
    except:
        os.system("mayapy -m pip install numpy") 
            
    try:
        import scipy
    except:
        os.system("mayapy -m pip install scipy")
              
    try:
        import PIL
    except:
        os.system("mayapy -m pip install Pillow")
            
    try:
        import matplotlib
    except:
        os.system("mayapy -m pip install matplotlib")
        
    scriptpath = getscriptpath()
    
    try:
        os.remove(scriptpath+"/Image2ANS.pyw")
        os.remove(scriptpath+"/Image2ANS.py")
    except:
        None
        
    with open(scriptpath+"/Image2ANS.pyw","w") as f:
        f.write(script)
        f.close()
        
    ICON = "extrude_NEX32.png"
    LNAME = "Image to AO, Normal and Specular"

    import maya.mel as mel

    topShelf = mel.eval('$nul = $gShelfTopLevel')
    currentShelf = cmds.tabLayout(topShelf, q=1, st=1)
    cmds.shelfButton(parent=currentShelf, c=buttonscript, label=LNAME, i=ICON)