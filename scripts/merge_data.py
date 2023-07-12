import numpy as np
import pandas as pd
from scipy.io import mmread

#Uses 10X gene expression and spot position info + CellSeg segmentation + scDINO CLS features output to create merged dataframes
#Writes out coords_with_spots.csv that assigns each segmented cell to a spot
#Writes out spos_feats.csv that includes spot coordinates, CLS tokens, average CLS token (each spot has inconsistent number of cells), and expression values for each gene

coords = "path_to_cell_coords.npz" #output of run_dino_prep.py
exp = "path/filtered_feature_bc_matrix/matrix.mtx" #gene exp matrix from 10X or other mtx with spot vs gene expression values
tissue_positions = "path/spatial/tissue_positions.csv" #10X csv that includes spot x and spot y values
cls = "path/CLS_features/channel_Iba_Vimentin_DAPI_Blank1_Blank2_model_sc-ViT_checkpoint0100_vitsmall16_features.csv" #scDINO CLS features output
output_dir = "directory" #directory to write coords_with_spots.csv and spots_feats.csv to

def load_spots(tissue_positions): 
	'''Cleans tissue_positions.csv from the 10X Visium space ranger pipeline. Returns pandas dataframe that includes 
	pixel X and Y coordinates of each in-tissue spot
	
	inputs:
	tissue_positions -- str -- path to tissue_positions.csv
	
	returns:
	spots -- pandas df -- dataframe of cleaned tissue positions to just include X and Y pixel values of in-tissue spots'''
	spots = pd.read_csv(tissue_positions, usecols=["in_tissue","pxl_row_in_fullres", "pxl_col_in_fullres"])#load tissue_positions.csv
	spots = spots[spots["in_tissue"]==1]
	spots = spots.drop(columns=["in_tissue"])
	spots = spots.reset_index()
	spots = spots.drop(columns=["index"])
	return spots

def assign_cell_to_spot(spots, coords, output_dir: str):
	'''Takes in spots pandas dataframe from load_spots and npz file with single cell coordinates named "coords"
	and returns pandas dataframe with pixel X coordinate column (column="X"), pixel Y coordinate column (column="Y"), and 
	column with single cell's spot assignment based on nearest distance (column="spot"). 
	Writes dataframe to coords_with_spots.csv.
	
	inputs:
	spots -- pandas df -- dataframe with pixel X and pixel Y columns for each in-tissue spot
	coords -- npz -- single cell coordinate file, npz index="coords"
	output_dir -- str -- path to directory to write coords_with_spots.csv to

	returns:
	coords_with_spot -- pandas df -- dataframe with "X", "Y", and "spot" column for each cell 
	'''
	coords = np.load(coords)
	coords = coords["coords"] #0=x, 1=y
	coord_spots = []
	for locs in range(coords.shape[1]):
		x_cell = coords[0][locs]
		y_cell = coords[1][locs]
		dists = []
		cell = np.array((x_cell,y_cell))
		for row in spots.iterrows():
			x_spot = row[1]["pxl_col_in_fullres"]
			y_spot = row[1]["pxl_row_in_fullres"] 
			spot = np.array((x_spot, y_spot))
			dist = np.linalg.norm(cell-spot) #calculate euclidean distance between points
			dists.append(abs(dist))
		spot = np.argmin(dists)
		coord_spots.append(spot)
	coords_with_spot = pd.DataFrame(coords.T, columns=["X","Y"])
	coords_with_spot["spot"]=coord_spots
	coords_with_spot.to_csv("%s/coords_with_spot.csv" % output_dir)
	return coords_with_spot #new df with spot column

def assign_spot_feats(coords_with_spot, cls, exp, spots):
	''' Merges coordinates, cls tokens, and gene expression into single dataframe.

	inputs:
	coords_with_spot -- pandas df -- dataframe with "X", "Y", and "spot" column for each cell (output of assign_cell_to_spot)
	cls -- str -- path to scDINO output for CLS feats ex) channel_Iba_Vimentin_DAPI_Blank1_Blank2_model_sc-ViT_checkpoint0100_vitsmall16_features.csv
	exp -- str --  path to 10x Visium filtered gene expression .mtx matrix ex) filtered_feature_bc_matrix/matrix.mtx
	spots -- dataframe of cleaned tissue positions to just include X and Y pixel values of in-tissue spots (output of load_spots)

	return:
	spot_feats -- pandas df --  dataframe of spot features: cols are "pxl_row_in_fullres" (spot center y), "pxl_col_in_fullres" (spot center x), 
	"CLS" (all CLS features for each spot), "CLS Norm" (normalized CLS token- 1 per spot), 
	and one column for each gene with spot-level expression values (col named by gene index from 10X)
	'''
	#load gene expression matrix rows=genes, cols=spots in tissue
	exp = mmread(exp)
	exp = exp.toarray()
	cls = np.loadtxt(cls, delimiter= ",") #load CLS features

	#Add CLS Features to spots
	all_cls = []
	mean_cls = []
	for spot in range(spots.shape[0]):
		cls_feats = []
		list = coords_with_spot[coords_with_spot['spot'] == spot].iloc[:,0].tolist()
		for idx in list:
			cls_feats.append(cls[idx,:])
		all_cls.append(cls_feats)
		mean_cls.append(np.mean(cls_feats, axis=0))
	spots["CLS"]=all_cls
	spots["CLS Norm"] = mean_cls
	print("CLS added")

	#Add ST gene expression to spots
	exp_df = pd.DataFrame(exp.T)
	print("Gene expression added")

	spot_feats = pd.concat([spots,exp_df], axis=1)
	return spot_feats

#spots = load_spots(tissue_positions)
#coords_with_spot = assign_cell_to_spot(spots,coords, output_dir)
#spot_feats = assign_spot_feats(coords_with_spot,cls, exp, spots)
#spot_feats.to_csv("%s/spot_feats.csv" % output_dir)