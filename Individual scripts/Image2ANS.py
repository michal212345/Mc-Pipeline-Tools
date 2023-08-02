import math, functools
import numpy as np
from scipy import ndimage
from matplotlib import pyplot
from PIL import Image, ImageOps,ImageEnhance
import os

def memorize(func):
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

    if max_y >= max_x:
        max_value = max_y

    if max_value == 0:
        max_value = 1

    normal_map = np.zeros((height, width, 3), dtype=np.float32)

    intensity = max(intensity, 0.0001)

    try:
        strength = max_value / (max_value * intensity)
    except ZeroDivisionError:
        strength = 1

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

def normalized(a) -> float: 
    if np.sum(a*a) == 0:
        return a
    factor = 1.0/math.sqrt(np.sum(a*a)) # normalize
    return a*factor

def my_gauss(im:np.ndarray):
    return ndimage.uniform_filter(im.astype(float), size=20)

def shadow(im:np.ndarray,shadowStrength = .5):
    
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
    mean = round(np.mean(shadow),5)
    rmse = round(np.sqrt(np.mean((shadow-mean)**2))*(min(1/shadowStrength,1)),5)
    shadow = np.clip(shadow, mean-rmse*2.0,mean+rmse*0.5)

    return shadow

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

def readPNG(path:str) -> np.ndarray:
    with Image.open(path,"r") as img:
        return np.array(img.convert("RGB"))/255

def NumpyToPillow(im:np.ndarray) -> Image:
    return Image.fromarray(np.uint8(im*255))

def CleanupAO(path:str):
    with Image.open(path) as img:
        red, green, blue, alpha= img.split()
        NewG = ImageOps.colorize(green,black=(100, 100, 100),white=(255,255,255),blackpoint=0,whitepoint=180)
        NewG.save(path, bitdepth=16)

def Convert(input_file:str, smoothness = 5, intensity = 5, dAO = True, doS = True, doN = True):
    """Converts the given image to a normal map and ambient occlusion map."""

    if input_file == None or input_file == "" or not input_file.endswith(".png"):
        raise ValueError("Invalid input file.")

    print('Doing: ',str(input_file))

    with Image.open(input_file,"r") as img:
        
        if doS == True:
            saturation = ImageEnhance.Color(img.convert("RGB"))

            saturation = saturation.enhance(0)
            brightnesscorect = ImageEnhance.Brightness(saturation)
            im_out = brightnesscorect.enhance(.75)
            im_out.save(adjustPath(input_file,"Spec"))
            print("Specular Done.")
        
        size = img.size
        sizen = list(size)
        
        if sizen[0] <= 2048 and sizen[1] <= 2048:

            print("Image is too small enough.")

            while sizen[0] <= 2047 and sizen[1] <= 2047:
                sizen[0] = sizen[0] * 2
                sizen[1] = sizen[1] * 2

            print("Resizing to: ",sizen)

            resized = img.resize((sizen[0],sizen[1]),Image.Resampling.NEAREST)
            temp_file = adjustPath(input_file,"Resized")
            resized.convert("RGB").save(temp_file)
            
            oldpath = input_file
            input_file = temp_file
            resized = True
        else:
            oldpath = input_file
            input_file = input_file

    if doN == True:
        im = readPNG(input_file)

        if im.ndim == 3:
            im_grey = np.zeros((im.shape[0],im.shape[1])).astype(float)
            im_grey = (im[...,0] * 0.3 + im[...,1] * 0.6 + im[...,2] * 0.1)
            im = im_grey

        im_smooth = smooth_gaussian(im, smoothness)

        sobel_x, sobel_y = sobel(im_smooth)

        normal_map = compute_normal_map(sobel_x, sobel_y, intensity)

        red, green, blue = NumpyToPillow(normal_map).split()
        Image.merge("RGB",(red,ImageOps.invert(green),blue)).save(adjustPath(oldpath,"Normal"), bitdepth=16)

        print("Normal Done.")

    if dAO == True:
        im_shadow = shadow(im)
        pyplot.imsave(adjustPath(oldpath,"AO"),im_shadow,cmap="gray")
        CleanupAO(adjustPath(oldpath,"AO"))
        print("Ambient Occlusion Done.")

    if resized == True:
        os.remove(temp_file)
        
    print("Done: ", input_file)