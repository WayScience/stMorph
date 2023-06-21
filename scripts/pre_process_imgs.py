import cv2
import numpy as np
import tifffile as tiff
import pandas as pd


img =  "/home/daynaolson/10x_prostate_run_croped_test/image/Visium_FFPE_Human_Prostate_IF_image.tif"
segs = "/home/daynaolson/10x_prostate_run_croped_test/output/quantifications/Visium_FFPE_Human_Prostate_IF_image_statistics_growth2_uncomp.csv"
output_dir = "/home/daynaolson/10x_prostate_run_croped_test/cell_crops"
box_size = 50

def crop_img(img, x,y, box_size, idx, output_dir="None"):
	'''Takes in multichannel img array and crops based on center coordinators and desired box size.

		inputs:
		img -- array -- original image to crop
		x -- int or float -- x pixel of orginal image to center crop
		y -- int or float -- y pixel of original image to center crop
		box_size -- int -- dimension of a box_size x box_size image that crop will result in
		idx -- int -- cell index for naming output image
		output_dir -- str -- output directory path'''
	
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

def img_to_cells(img, segs, x_center_col, y_center_col, box_size, output_dir):
	'''Takes in pre-segmented multichannel, saves each cell as an individual image in tiff format of a specified box size, and returns list of cell image arrays.

		inputs:
		img -- tif -- original tiff image
		segs -- csv -- contains segmentation information (particular x and y centers for each cell)
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
