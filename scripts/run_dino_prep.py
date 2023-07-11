from pre_process import run_cell_seg
from pre_process import prep_dino

#Runs all necessary prep steps for entrance into scDINO pipeline including cellsegmentation using CellSeg and cropping images by cell.
#Image tiling may be necessary for segmentation if image file very large. If tiling not needed, set numx and numy to 1.
#Note: Need to be run in the cellsegsegmenter conda enviornment https://michaellee1.github.io/CellSegSite/windows-install.html

img =  # "Path to image tiff file"
output_dir = #"Output directory for cell segmentation and crops". 
numx = 4 #Number of tiles along x-axis of image
numy = 2 #Number of tiles along y-axis of image
channel_names =  #Text file for image channel names"
add_channels = True #Add empty channels to images
num_channels = 2 #Adding 2 channels to 3 channel cell images to be compatible with pretraind scDINO 5 channel model

run_cell_seg(img, output_dir, numx,numy,channel_names)
prep_dino(img, "%s/output/quantifications" % output_dir ,4,2,2,50, "%s/cell_crops" % output_dir, add_channels, num_channels)

