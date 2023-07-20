#!/usr/bin/env python
# coding: utf-8

# In[1]:


from numba import NumbaDeprecationWarning, NumbaPendingDeprecationWarning
import warnings
warnings.simplefilter('ignore', category=NumbaDeprecationWarning)
warnings.simplefilter('ignore', category=NumbaPendingDeprecationWarning)
import anndata as ad
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scanpy as sc
import seaborn as sns
import sklearn.cluster as cluster
import umap


# In[2]:


data = pd.read_csv("spot_feats.csv") #load data from merge_data.py output
data = data.dropna()


# In[3]:


import matplotlib.pyplot as plt
plt.rcParams.update({'font.size': 20})


# ## Exp preprocessing Taken From: https://scanpy-tutorials.readthedocs.io/en/latest/spatial/basic-analysis.html#QC-and-preprocessing

# # Clustering CLS Tokens
# ### CLS tokens derived from scDINO vision transformer and normalized to the spot level

# In[4]:


cls_vals = data.filter(regex='^i',axis=1)
cls = sc.AnnData(cls_vals)
sc.pp.pca(cls)
sc.pp.neighbors(cls)
sc.tl.umap(cls)
sc.tl.leiden(cls, key_added="clusters")
sc.pl.umap(cls, color=["clusters"], wspace=0.4)


# # Clustering Gene Expression

# In[5]:


exp_vals = data.filter(regex='^e',axis=1)
exp = sc.AnnData(exp_vals)
sc.pp.filter_genes(exp, min_cells=10)
sc.pp.normalize_total(exp, inplace=True)
sc.pp.log1p(exp)
sc.pp.highly_variable_genes(exp, flavor="seurat", n_top_genes=2000)

sc.pp.pca(exp)
sc.pp.neighbors(exp)
sc.tl.umap(exp)
sc.tl.leiden(exp, key_added="clusters")

sc.pl.umap(exp, color=["clusters"], wspace=0.4)


# # Clustering CLS Tokens + Gene Expression

# In[6]:


cls_new = sc.AnnData(cls_vals)

exp_new = sc.AnnData(exp_vals)
sc.pp.filter_genes(exp_new, min_cells=10)
sc.pp.normalize_total(exp_new, inplace=True)
sc.pp.log1p(exp_new)
sc.pp.highly_variable_genes(exp_new, flavor="seurat", n_top_genes=2000)

comb_vals = pd.concat([data.filter(regex='^i',axis=1), data.filter(regex='^e',axis=1)], axis=1)
comb = ad.concat([cls_new, exp_new], axis=1,join="inner") #only expression is pre-processed with scanpy

sc.pp.pca(comb)
sc.pp.neighbors(comb)
sc.tl.umap(comb)
sc.tl.leiden(comb, key_added="clusters")

sc.pl.umap(comb, color=["clusters"], wspace=0.4)


# # Tissue Plotting
# 
# ###  Spots plotted by tissue coordinates, colored by cluster 

# In[7]:


cls_df = pd.Series(np.array(cls.obs["clusters"],dtype="int"), name="clusters")
cls_tissue = pd.concat([data["pxl_row_in_fullres"],data["pxl_col_in_fullres"],cls_df], axis=1)
sns.scatterplot(x='pxl_col_in_fullres', y='pxl_row_in_fullres', data=cls_tissue, hue='clusters', palette='tab10', s=16)
plt.xlabel('x-coodinate')
plt.ylabel('y-coordinate')
plt.title("CLS Tokens Only")
plt.gca().invert_yaxis()
plt.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0., ncols=2)
plt.show()


# In[8]:


exp_df = pd.Series(np.array(exp.obs["clusters"],dtype="int"), name="clusters")
exp_tissue = pd.concat([data["pxl_row_in_fullres"],data["pxl_col_in_fullres"],exp_df], axis=1)
sns.scatterplot(x='pxl_col_in_fullres', y='pxl_row_in_fullres', data=exp_tissue, hue='clusters', palette='tab10', s=16)
plt.xlabel('x-coodinate')
plt.ylabel('y-coordinate')
plt.title("Gene Expression Only")
plt.gca().invert_yaxis()
plt.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0., ncols=2)
plt.show()


# In[9]:


comb_df = pd.Series(np.array(comb.obs["clusters"],dtype="int"), name="clusters")
comb_tissue = pd.concat([data["pxl_row_in_fullres"],data["pxl_col_in_fullres"],comb_df], axis=1)
sns.scatterplot(x='pxl_col_in_fullres', y='pxl_row_in_fullres', data=comb_tissue, hue='clusters', palette='tab10', s=16,)
plt.xlabel('x-coodinate')
plt.ylabel('y-coordinate')
plt.title("CLS Tokens + Gene Expression")
plt.gca().invert_yaxis()
plt.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0., ncols=2)
plt.show()

