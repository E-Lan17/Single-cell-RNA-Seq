
import os
import cello
import numpy as np
import scanpy as sc
import seaborn as sns
from matplotlib.pyplot import rc_context
import warnings
warnings.filterwarnings('ignore')
sc.set_figure_params(dpi=100)


out = []
for file in os.listdir('/home/XXX/Documents/Résultats/23-11-01_RNAseq/raw_counts/'):
    adata = sc.read_h5ad('/home/XXX/Documents/Résultats/23-11-01_RNAseq/raw_counts/'+file).T
    adata = adata.transpose() # H5AD FROM SEURAT !!!!!!!!
    #adata[:, adata.var_names.str.match('GNAS')]
    adata.var_names_make_unique()   
    adata.obs['Sample'] = file

    #PREFILTRE and ID
    sc.pp.filter_cells(adata, min_genes=200) #get rid of cells with fewer than 200 genes
    sc.pp.filter_genes(adata, min_cells=10) #get rid of genes that are found in fewer than 10 cells
    adata.var['mt'] = adata.var_names.str.startswith('MT-')  # annotate the group of mitochondrial genes as 'mt'  
    adata.var["ribo"] = adata.var_names.str.startswith(("RPS", "RPL")) # annotate the group of ribo genes as 'ribo'
    
    #METRIC
    sc.pp.calculate_qc_metrics(adata, qc_vars=['mt','ribo'], percent_top=None, log1p=True, inplace=True)
    sc.pl.violin(adata, ['pct_counts_mt','pct_counts_ribo'],jitter=0.4, multi_panel=True)
    sns.displot(adata.obs["total_counts"], bins=100, kde=False)
    sc.pl.scatter(adata, "total_counts", "n_genes_by_counts", color="pct_counts_mt")
    
    #FILTRE
    adata = adata[adata.obs.pct_counts_mt < 5] # remove outliner cells by gene mt (5%)
    #adata = adata[adata.obs.pct_counts_ribo < 15] # remove outliner cells by gene ribo DANGEROUS !!
    upper_lim = np.quantile(adata.obs.n_genes_by_counts.values, .98) #get rid of upper outliner
    lower_lim = np.quantile(adata.obs.n_genes_by_counts.values, .02) #get rid of lower outliner
    adata = adata[(adata.obs.n_genes_by_counts < upper_lim)]
    adata = adata[(adata.obs.n_genes_by_counts > lower_lim)] #sometimes can remove all the sample
    #FILTRE MITO  
    keep = adata.var_names[adata.var.mt==False]
    adata = adata[:,adata.var_names.isin(keep)]

    #DOUBLETS REMOVAL
    ##sc.pp.highly_variable_genes(adata, min_mean=0.0125, max_mean=3, min_disp=0.5)
    ##adata = adata[:, adata.var.highly_variable]
    ##sc.pp.highly_variable_genes(adata, n_top_genes=5000, subset=True, flavor= "seurat")
    #adata_sim = sc.external.pp.scrublet_simulate_doublets(adata) # create model for doublet
    #sc.external.pp.scrublet(adata,adata_sim=adata_sim) #apply model for doublet 
    ##Subset doublet or keep them to observe later
    #adata.obs['predicted_doublet'].value_counts()
    ##adata_T = adata[(adata.obs.predicted_doublet == "False")]
    
    #NORMALISE CELO or NORMAL
    #CELO
    #sc.pp.normalize_total(adata, target_sum=1e6) #normalize every cell to 10^6 UMI
    #sc.pp.log1p(adata) #change to log counts
    #sc.pp.highly_variable_genes(adata, n_top_genes=10000)
    #sc.pp.pca(adata,n_comps=50,use_highly_variable=True)
    #sc.pp.neighbors(adata, n_neighbors=15)
    #sc.tl.leiden(adata, resolution=2.0)
    #NORMAL
    sc.pp.normalize_total(adata, target_sum=1e6,exclude_highly_expressed=True) #normalize every cell to 10,000 UMI
    sc.pp.log1p(adata) #change to log counts
    #sc.pp.highly_variable_genes(adata, n_top_genes=3000, flavor= "seurat") 
    #sc.pp.highly_variable_genes(adata, min_mean=0.0125, max_mean=3, min_disp=0.5)
    #adata = adata[:, adata.var.highly_variable]   
    ##sc.pp.regress_out(adata, ['total_counts', 'pct_counts_mt']) #Regress out effects of total counts per cell and the percentage of mitochondrial genes expressed
    ##sc.pp.scale(adata, max_value=10) #scale each gene to unit variance
    ##sc.tl.pca(adata, svd_solver='arpack') #juste for PCA use scale
    sc.pp.neighbors(adata, n_neighbors=10, n_pcs=20)
    sc.tl.leiden(adata, resolution = 0.25)
    sc.tl.umap(adata)
    
    out.append(adata)

del (adata,file,lower_lim,upper_lim) #,adata_sim

#CELLO CLUSTER
# https://star-protocols.cell.com/protocols/945#limitations
#cello_resource_loc = os.getcwd()
#for file in out :
#    model_prefix = "Pancreat_Cancer"
#    cello.scanpy_cello(adata,clust_key='leiden',rsrc_loc=cello_resource_loc,
#                   out_prefix=model_prefix, log_dir=os.getcwd())
#    sc.tl.umap(adata)
#    sc.pl.umap(adata, color='leiden', title='Clusters')
#    sc.pl.umap(adata, color='Most specific cell type')
  
#MANUAL CLUSTER
for file in out :
    with rc_context({'figure.figsize': (4, 4)}):
        sc.pl.umap(file, color = ['leiden'], frameon = False, title = str("Orphan GPCR in pancreatic adenocarcinome")) # , legend_loc = None)

#PLOT
markers_Orphan = ["GPR3","GPR4","GPR6","GPR12","GPR15","GPR17","GPR20","GPR22","PR26",
           "GPR31","GPR34","GPR35","GPR37","GPR39","GPR50","GPR63","GPR65",
           "GPR68","GPR75","GPR84","GPR87","GPR88","GPR132","GPR149","GPR161",
           "GPR183","LGR4","LGR5","LGR6","MAS1","MRGPRD","MRGPRX1","MRGPRX2",
           "P2RY10","TAAR2","GPR156", "GPR158", "GPR179", "GPRC5A", "GPRC5B",
           "GPRC5C", "GPRC5D", "GPRC6" ]

for file in out :
    list_gene_Orphan= []
    
    for genes in markers_Orphan : 
        df = file.var_names
        if genes in df :
            list_gene_Orphan.append(genes)      
    sc.pl.dotplot(file,list_gene_Orphan ,groupby=['orig.ident'], use_raw=False,
                  mean_only_expressed= True,standard_scale="var", vmax=1, vmin =0,
                  title=("Orphan GPCR in pancreatic adenocarcinome")) 

#SAVE
for file in out :
    save_file = "/home/XXX/Documents/Résultats/23-11-01_RNAseq/raw_counts/Filtered_"+ str(file.obs['Sample'][0])
    file.write_h5ad(save_file)

#INTEGRATION incomplete
#adata_copy = out[0][out[0].obs["orig.ident"].str.startswith('N'),:]
#out[1].obs.rename(columns={"patient": "orig.ident"}, inplace=True)
#var_names = out[1].var_names.intersection(out[0].var_names)
#adata_copy = adata_copy[:, var_names]
#out[1] = out[1][:, var_names]
#out[1] = out[1].concatenate(adata_copy)
#for adata in final :
#    adata = sc.pp.combat(adata, key="orig.ident")

#SUBSET
#adata = adata[adata.obs["orig.ident"].isin(["sc5rJUQ026","sc5rJUQ033","sc5rJUQ039","sc5rJUQ042","sc5rJUQ043","sc5rJUQ045","sc5rJUQ046" 
#"sc5rJUQ050","sc5rJUQ051","sc5rJUQ053","sc5rJUQ058","sc5rJUQ060","sc5rJUQ064","scrJUQ058" 
#"scrJUQ059","scrJUQ068","scrJUQ070","scrJUQ072"])]

#LOAD
out=[]
file = sc.read_h5ad("/home/XXX/Documents/Résultats/23-11-01_RNAseq/Process/Pancreatic_ductal_adenocarcinoma/Filtered_pancreatic_ductal_adenocarcinoma_PRJCA001063.h5ad").T
file = file.transpose()
out.append(file)
