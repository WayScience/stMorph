import os
import sys
import numpy as np
import pandas as pd
import tifffile as tiff
import shutil
from orig_tiff import OrigTiff
sys.path.append('CellSeg')
from CellSeg import main


def cell_seg_prep(img:tiff, output_dir, numx:int,numy:int,channel_names):
	'''Prepares image for CellSeg including tiling. Returns output_dir path that includes tiles and output subfolders.

	inputs:
	img -- str -- path to tiff image to crop
	output_dir -- str -- path to directory one up of desired tiles and CellSeg output directories.
	numx -- int -- number of tiles to divide image into on x-axis
	numy -- number of tiles to divide image into on y-axis (for example, if numx=4 and numy=2 the image will be cropped into tiles by a 4x2 grid)
	channel_names -- str -- path to text file that includes each image channel name as a line in order
	
	returns:
	target -- str -- path to project directory'''


	if not os.path.exists(output_dir):
		os.mkdir(output_dir)
	if not os.path.exists("%s/tiles" % output_dir):
		os.mkdir("%s/tiles" % output_dir)
	if not os.path.exists("%s/output" % output_dir):
		os.mkdir("%s/output" % output_dir)

	tif = OrigTiff(img,numx,numy)
	tif.crop_tif("%s/tiles" % output_dir)
	if not os.path.exists("%s/channelNames.txt" % output_dir):
		shutil.copyfile(channel_names, "%s/channelNames.txt" % output_dir)
	target = output_dir
	return target

def run_cell_seg(img:tiff, output_dir, numx:int,numy:int,channel_names):
	'''Prepares image for CellSeg and runs CellSeg using the submodule.

	inputs:
	img -- str -- path to tiff image to crop
	output_dir -- str -- path to directory one up of desired tiles and CellSeg output directories.
	numx -- int -- number of tiles to divide image into on x-axis
	numy -- number of tiles to divide image into on y-axis (for example, if numx=4 and numy=2 the image will be cropped into tiles by a 4x2 grid)
	channel_names -- str -- path to text file that includes each image channel name as a line in order'''

	target = cell_seg_prep(img,output_dir,numx,numy,channel_names)
	main.main(target)

def merge_coords(coord_dir, tile_names, xbounds:float, ybounds:float, x_name:str, y_name:str, output_dir: str):
	'''Converts CellSeg-segmetned tile cell center coordinates to coordinates in original image. Returns path to csv that contains cell coordiantes for the entire image.

	inputs:
	coord_dir -- str -- path to directory that contains CellSeg coordinate output files.
	tile_names -- list of str -- list of image tile names, using the OrigTiff tile naming convention
	xbounds -- list of float-- list of pixel x values for tile boundaries in terms of the entire image
	ybounds -- list of float -- list of pixel y values for tile boundaries in terms of the entire image
	x_name -- name of column in the coordinate file that contains cell center x coordinates in terms of the individual tile
	y_name -- name of column in the coordinate file that contains cell center y coordinates in terms of the individual tile
	output_dir -- str -- path to directory to output full coordinate file'
	
	returns:
	path -- str -- path to file with all cell coordinates'''
	isExist = os.path.exists(output_dir)
	if not isExist:
		os.makedirs(output_dir)
	X = []
	Y = []
	for name in tile_names:
		data = pd.read_csv("%s/%s__statistics_growth2_uncomp.csv" % (coord_dir, name), usecols=[x_name,y_name])
		x_offset = xbounds[int(name[3]-1)]
		y_offset = ybounds[int(name[2]-1)]
		x = np.array(data[x_name]) + x_offset
		y = np.array(data[y_name]) + y_offset
		X.append(x)
		Y.append(y)
	X_all = [item for sublist in X for item in sublist]
	Y_all = [item for sublist in Y for item in sublist]
	coords = np.array((X_all, Y_all))
	path = "%s/cell_coords.npz" % output_dir
	np.savez("%s/cell_coords.npz" % output_dir, coords=coords)
	return path

def crop_cell(img: np.array, x: int or float, y: int or float, box_size: int, idx: int, num_channels:int, output_dir: str = "None",  add_channels=False) -> np.array:
	'''Takes in multichannel img array and crops cell at specified center coordinates as an  individual image with a desired box size. Returns cropped image array. 
	Can add specified number of empty (zero-filled) image channels to be compatible with pre-trained multi-channel vision transformer models.

	inputs:
	img -- array -- original image to crop
	x -- int or float -- x pixel of orginal image to center crop
	y -- int or float -- y pixel of original image to center crop
	box_size -- int -- dimension of a box_size x box_size image that crop will result in
	idx -- int -- cell index for naming output image
	output_dir -- str -- output directory path (optional-if set to none the image array will be returned but the .tif image will not be saved.
	add_channels -- bool -- If true, adds num_channel number of zero-filled channels to image. 
	num_channels -- int -- Number of zero-filled channels to add to image. 
	
	returns: 
	crop -- np array -- cropped image array for single cell'''

	#Get rectangle boundaries
	x = np.round(x)
	y = np.round(y)
	
	xmin = int(x - (box_size/2)) 
	xmax = int(x + (box_size/2)) 
	ymin = int(y - (box_size/2)) 
	ymax = int(y + (box_size/2)) 

	# crop the image at the bounds
	crop = img[:,ymin:ymax, xmin:xmax]
	if add_channels == True:
		zeros = np.zeros((num_channels, box_size, box_size))
		crop = np.concatenate((crop, zeros))
	if output_dir != "None":
		tiff.imwrite("%s/cell_%i.tif" % (output_dir, idx), crop.astype('float32'), imagej=True)
	return crop

def img_to_cells(img: tiff, segs, box_size: int, output_dir: str, num_channels:int,add_channels=False):
	'''Takes in pre-segmented multichannel and saves each cell as an individual image in tiff format of a specified box size.
	Can add specified number of empty (zero-filled) image channels to be compatible with pre-trained multi-channel vision transformer models.

	inputs:
	img -- str -- path to original tiff image
	segs -- csv -- path to array (npz) that contains segmentation information (particular x and y centers for each cell under "coords")
	box_size -- int -- desired image size for cell crops
	output_dir -- str -- desired output directory path
	add_channels -- bool -- If true, adds num_channel number of zero-filled channels to image. 
	num_channels -- int -- Number of zero-filled channels to add to image. '''
	segs = np.load(segs)
	segs = segs["coords"]
	img = tiff.imread(img)
	for i in range(segs.shape[1]):
		crop_cell(img, segs[0,i], segs[1,i], box_size, i, num_channels, output_dir, add_channels)

def prep_dino(img:tiff, coord_dir, numx:int, numy:int, nuclei_channel:int, boxsize:int, output_dir: str, num_channels:int, add_channels=False):
	'''Crops tiff into single cell images for use in scDINO.
	Can add specified number of empty (zero-filled) image channels to be compatible with pre-trained scDINO 5 channel model.


	inputs:
	img -- str -- path to tiff image
	coord_dir -- str -- path to directory that contains CellSeg coordinate output files.
	numx -- int -- number of tiles to divide image into on x-axis
	numy -- number of tiles to divide image into on y-axis (for example, if numx=4 and numy=2 the image will be cropped into tiles by a 4x2 grid)
	nuclei_channel -- int -- image channel that includes nuclei staining
	boxsize -- int -- desired boxsize x boxsize size of cropped cell images
	output_dir -- str -- path to output directory for cell crops
	add_channels -- bool -- If true, adds num_channel number of zero-filled channels to image. 
	num_channels -- int -- Number of zero-filled channels to add to image.'''
	
	isExist = os.path.exists(output_dir)
	if not isExist:
		os.makedirs(output_dir)

	tif = OrigTiff(img,numx,numy)
	xbounds, ybounds = tif.get_bounds()
	files = tif.get_tile_names()
	coords = merge_coords(coord_dir, files,  xbounds, ybounds, "Absolute X", "Absolute Y", output_dir)
	img_to_cells(img, coords, boxsize, output_dir, num_channels, add_channels)

