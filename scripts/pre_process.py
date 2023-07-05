import numpy as np
import tifffile as tiff
import pandas as pd
import os
import orig_tiff

img = "/home/daynaolson/10x_prostate_run/Visium_FFPE_Human_Prostate_IF_image.tif"
crop_tif_x = 4
crop_tif_y = 2



def merge_coords():



def crop_cell(img: np.array, x: int or float, y: int or float, box_size: int, idx: int, output_dir: str = "None") -> np.array:
	'''Takes in multichannel img array and crops cell at specified center coordinates as an  individual image with a desired box size. Returns cropped image array.

		inputs:
		img -- array -- original image to crop
		x -- int or float -- x pixel of orginal image to center crop
		y -- int or float -- y pixel of original image to center crop
		box_size -- int -- dimension of a box_size x box_size image that crop will result in
		idx -- int -- cell index for naming output image
		output_dir -- str -- output directory path (optional-if set to none the image array will be returned but the .tif image will not be saved.'''
	
	#Get rectangle boundaries
	x = np.round(x)
	y = np.round(y)
	
	xmin = int(x - (box_size/2)) 
	xmax = int(x + (box_size/2)) 
	ymin = int(y - (box_size/2)) 
	ymax = int(y + (box_size/2)) 

	# crop the image at the bounds
	crop = img[:,ymin:ymax, xmin:xmax]

	if output_dir != "None":
		tiff.imwrite("%s/cell_%i.tif" % (output_dir, cell_idx), crop, imagej=True)
	return crop

def img_to_cells(img: tiff, segs: csv, x_center_col: str y_center_col: str, box_size: int, output_dir: str):
	'''Takes in pre-segmented multichannel, saves each cell as an individual image in tiff format of a specified box size, and returns list of cropped cell image arrays.

		inputs:
		img -- str -- path to original tiff image
		segs -- csv -- path to CSV that contains segmentation information (particular x and y centers for each cell)
		x_center_col -- str -- name of csv column that contains x centers for each cell
		y_center_col -- str -- name of csv column that contains y centers for each cell
		box_size -- int -- desired image size for cell crops
		output_dir -- str -- desired output directory path'''
	segs = pd.read_csv(segs, usecols=[x_center_col, y_center_col])
	img = tiff.imread(img)
	cell_imgs = []
	for index, data in segs.iterrows():
		cell = crop_img(img, data[x_center_col], data[y_center_col], box_size, index, output_dir)
		cell_imgs.append(cell)
	return cell_imgs

def prep_scDino(img, num_x, num_y, box_size, output_dir="./cell_segs"):
	coords = merge_coords(img, num_x, num_y)
	cell_imgs = img_to_cells(img, coords, "X", "Y", box_size, output_dir)
	return cell_imgs
