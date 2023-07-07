import numpy as np
import tifffile as tiff
import pandas as pd
import os

class OrigTiff:
	def __init__(self, img, num_x, num_y):
		'''Original tiff image. This class assumes the image was divided into equal crops along the x and y image axes for cell segmentation purposes.

		inputs:
    	img -- str -- path to original tiff image
    	num_x -- int -- number of segments along x-axis to divide image into
    	num_y -- int -- number of segments along y-axis to divide image into'''
		self.img = tiff.imread(img)
		self.num_x = num_x
		self.num_y = num_y

	def get_bounds(self):
		'''Returns bounds for each crop in reference to the original image, assuming division was done equally along each axis.'''
		xbounds = []
		ybounds = []
		for i in range(self.num_x):
			xbounds.append(int(i*self.img.shape[2]/self.num_x))
		xbounds.append(self.img.shape[2])
		for j in range(self.num_y):
			ybounds.append(int(j*self.img.shape[1]/self.num_y))
		ybounds.append(self.img.shape[1])
		return(xbounds, ybounds)

	def crop_tif(self, output_dir: str = "."):
		'''Crops the tiff into the specified number of segments, in order to use segmentation software without crashing. Creates new directory for each segment and writes segment to tif.

		inputs:
    	output_dir -- str -- output directory path for project (one up from desired tiff crop directories)'''
		xbounds, ybounds = self.get_bounds()
		for i in range(1,self.num_x+1):
			for j in range(1,self.num_y+1):
				isExist = os.path.exists("%s/%i%i" % (output_dir, j, i))
				if not isExist:
					os.makedirs("%s/%i%i/image" % (output_dir, j, i))
				crop = self.img[:, ybounds[j-1]:ybounds[j],xbounds[i-1]:xbounds[i]]
				tiff.imwrite("%s/%i%i/image/image.tif" % (output_dir, j, i), crop, imagej=True)

	def get_tile_names(self):
		'''Returns list of directories of tiff crops, assuming self.crop_tif() was used to create directories'''
		'''Returns list of cropped tile fil enames, assuming self.crop_tif() was used to create tiles.'''
		dirs = []
		tiles = []
		for i in range(1, self.num_x+1):
		for i in range(1, self.num_x+1):
			for j in range(1, self.num_y+1):
			for j in range(1, self.num_y+1):
				dirs.append("./%i%i" % (i,j))
				tiles.append("%i%i.tif" % (j,i))
		return dirs
		return tiles
