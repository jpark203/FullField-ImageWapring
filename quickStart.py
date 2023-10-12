## This code demonstrates how you can use the defined functions to warp an image.

# import functions and libraries
import MRIWarp as warp
import pandas as  pd


#----------------------------- compute the shape of screen
# set up inputs
pointFile = 'test_pointFile.csv' # replace it with your dispaly screen coordinates
remapfile = 'remapFile.csv' # name the output file from the function
projx = 3840 # dimension of the projection device (projector display resolution)
projy = 2160 
imagex = 1024 # dimension of the image to be warped (example image is 1024 x 768 pixels)
imagey = 768
yexpansion = 0.86 # interpolation factor used in determining equal segment lengths for ellipse arcs
upsample = 50

# compute the remapping 
# note: this step takes a while, but unless something is changed in the scanner toom, this needs to be done only once
remap = warp.CalcWarpRemap(pointFile, remapfile, projx, projy, imagex, imagey, yexpansion, upsample)



#---------------------- warp images
# warp the image by remapping the pixels from original image to a new image, based on the LUT
orgImgFile = 'test_inputImage.png' # an image file to warp
newImgFile = 'outputImage.png' # name the output image file
width = projx
height = projy

# read in the look up table (remap file)
remap_temp = pd.read_csv(remapfile, sep=',', header=None, skip_blank_lines=False)
remap = remap_temp.to_numpy('int16')

# warp and save the image to a new file
warp.remapImageFile(orgImgFile, remap, width, height, newImgFile)