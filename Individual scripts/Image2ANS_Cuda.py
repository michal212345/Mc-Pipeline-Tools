import cupy, os, numpy as np
from cupyx.scipy import ndimage as CudaImage
from matplotlib import pyplot
from PIL import Image, ImageOps,ImageEnhance

def smooth_gaussian(im:cupy.ndarray, sigma) -> cupy.ndarray:

    if sigma == 0:
        return im

    im_smooth = im.astype(float)
    kernel_x = cupy.arange(-3*sigma,3*sigma+1).astype(float)
    kernel_x = cupy.exp((-(kernel_x**2))/(2*(sigma**2)))

    im_smooth = CudaImage.convolve(im_smooth, kernel_x[cupy.newaxis])

    im_smooth = CudaImage.convolve(im_smooth, kernel_x[cupy.newaxis].T)

    return im_smooth

def gradient(im_smooth:cupy.ndarray):

    gradient_x = im_smooth.astype(float)
    gradient_y = im_smooth.astype(float)

    kernel = cupy.arange(-1,2).astype(float)
    kernel = - kernel / 2

    gradient_x = CudaImage.convolve(gradient_x, kernel[cupy.newaxis])
    gradient_y = CudaImage.convolve(gradient_y, kernel[cupy.newaxis].T)

    return gradient_x,gradient_y


def sobel(im_smooth):
    gradient_x = im_smooth.astype(float)
    gradient_y = im_smooth.astype(float)

    kernel = cupy.array([[-1,0,1],[-2,0,2],[-1,0,1]])

    gradient_x = CudaImage.convolve(gradient_x, kernel)
    gradient_y = CudaImage.convolve(gradient_y, kernel.T)

    return gradient_x,gradient_y


def compute_normal_map(gradient_x:cupy.ndarray, gradient_y:cupy.ndarray, intensity=1):

    width = gradient_x.shape[1]
    height = gradient_x.shape[0]
    max_x = cupy.max(gradient_x)
    max_y = cupy.max(gradient_y)

    max_value = max_x

    if max_y > max_x:
        max_value = max_y

    normal_map = cupy.zeros((height, width, 3), dtype=cupy.float32)

    intensity = 1 / intensity

    strength = max_value / (max_value * intensity)

    normal_map[..., 0] = gradient_x / max_value
    normal_map[..., 1] = gradient_y / max_value
    normal_map[..., 2] = 1 / strength

    norm = cupy.sqrt(cupy.power(normal_map[..., 0], 2) + cupy.power(normal_map[..., 1], 2) + cupy.power(normal_map[..., 2], 2))

    normal_map[..., 0] /= norm
    normal_map[..., 1] /= norm
    normal_map[..., 2] /= norm

    normal_map *= 0.5
    normal_map += 0.5

    return normal_map

def normalized(a) -> float: 
    factor = 1.0/cupy.sqrt(cupy.sum(a*a)) # normalize
    return a*factor

def my_gauss(im:cupy.ndarray):
    return CudaImage.uniform_filter(im.astype(float),size=20)

def shadow(im:cupy.ndarray):
    
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
    mean = cupy.mean(shadow)
    rmse = cupy.sqrt(cupy.mean((shadow-mean)**2))*(1/shadowStrength)
    shadow = cupy.clip(shadow, mean-rmse*2.0,mean+rmse*0.5)

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
        im = cupy.array(pyplot.imread(input_file))

        if im.ndim == 3:
            im_grey = cupy.zeros((im.shape[0],im.shape[1])).astype(float)
            im_grey = (im[...,0] * 0.3 + im[...,1] * 0.6 + im[...,2] * 0.1)
            im = im_grey

        im_smooth = smooth_gaussian(im, smoothness)

        sobel_x, sobel_y = sobel(im_smooth)

        normal_map = compute_normal_map(sobel_x, sobel_y, intensity)

        pyplot.imsave(adjustPath(oldpath,"Normal"),np.array(normal_map.get()))

        flipgreen(adjustPath(oldpath,"Normal"))
        print("Normal Done.")

    if dAO == True:
        im_shadow = shadow(im)

        pyplot.imsave(adjustPath(oldpath,"AO"),np.array(im_shadow.get()))
        CleanupAO(adjustPath(oldpath,"AO"))
        print("Ambient Occlusion Done.")

    if resized == True:
        os.remove(temp_file)
        
    print("Done: ", input_file)