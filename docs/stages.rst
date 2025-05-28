```rst
.. contents::
   :local:
   :depth: 2

=============================
User Step By Step Guide
=============================

1. Inspect the Dataset Spreadsheet
----------------------------------
- Open the “DataSet” spreadsheet.
- Understand that each row represents one ground survey (a plot of land the British government surveyed).
- Note that the “Sorted plots” tab shows maps with the plane’s flight trajectory overlaid on each plot.

2. Create a Configuration File
------------------------------
A configuration (YAML) file tells the pipeline:
- Where to find the raw images.
- Where to save intermediate caches and final outputs.

2.1 Example Paths

.. code-block:: yaml

   # Path to store downloaded/cached image features
   img_cache_folder: /scratch/groups/smhsiang/ahp/stitching/cache/Zambia/c82e/SURF

   # Path to store intermediate checkpoints
   checkpoint_cache_folder: /oak/stanford/groups/smhsiang/aerialhist/stitching/results/Zambia/c82e

   # Path to write the final stitched raster output
   raster_output_folder: /oak/stanford/groups/smhsiang/aerialhist/stitching/results/Zambia/c82e

2.2 Create Your New Config

.. code-block:: bash

   find ~+ -type d -name "NCAP_DOS_53_GA*" | sort
   cp gambia_124.yml gambia_53.yml

- Edit **gambia_53.yml**:
  - Update `img_cache_folder`, `checkpoint_cache_folder`, and `raster_output_folder` as above.
  - **Add** at the bottom:

    .. code-block:: yaml

       digitized_plot: /oak/stanford/groups/smhsiang/aerialhist/datasets/scan_lines/Gambia/Gambia_scan_lines.csv

3. Sorted Plots Stage
---------------------
Download the DOS_PLOTS for Gambia onto your computer and point the config at it.

3.1 Update Config

.. code-block:: yaml

   # At the bottom of gambia_53.yml
   digitized_plot: /oak/stanford/groups/smhsiang/aerialhist/datasets/DOS_PLOTS/Gambia

3.2 Prepare SLURM Script

.. code-block:: bash

   cp slurm_initialize.sh slurm_sorted_plots.sh

- In **slurm_sorted_plots.sh**:
  
  .. code-block:: text

     #SBATCH -p dev          # use DEV partition
     # (remove any “#SBATCH -c N” line so it defaults to 1 CPU)
  
  .. code-block:: bash

     singularity run /oak/stanford/groups/smhsiang/aerialhist/stitching/containers/surf_ceres.sif \
         python3 /home/users/sidsur/aerial-history-stitching/main.py \
         --config /oak/stanford/groups/smhsiang/aerialhist/stitching/config/Gambia/gambia_53.yml \
         --stage initialize-from-plots

- Submit:

  .. code-block:: bash

     sbatch slurm_sorted_plots.sh

4. New Neighbors Stage
----------------------
Compute pairwise links **within** each cluster (here, the two largest).

4.1 Prepare SLURM Script

.. code-block:: bash

   cp slurm_crop.sh slurm_new_neighbors.sh

- In **slurm_new_neighbors.sh**:
  
  .. code-block:: text

     #SBATCH -p serc,normal  # need more CPUs
     #SBATCH -c 30           # 30 CPUs
  
  .. code-block:: bash

     singularity run /oak/stanford/groups/smhsiang/aerialhist/stitching/containers/surf_ceres.sif \
         python3 /home/users/sidsur/aerial-history-stitching/main.py \
         --config /oak/stanford/groups/smhsiang/aerialhist/stitching/config/Gambia/gambia_53.yml \
         --stage new-neighbors \
         --ids -2             # “-2” picks the two largest clusters

- Submit:

  .. code-block:: bash

     sbatch slurm_new_neighbors.sh

5. Initialize Graph Stage
--------------------------
Use the computed links to create connected components.

5.1 Prepare SLURM Script

.. code-block:: bash

   cp slurm_crop.sh slurm_init_graph.sh

- In **slurm_init_graph.sh**:
  
  .. code-block:: text

     #SBATCH -p dev         # lightweight—DEV partition
     #SBATCH -c 1           # 1 CPU
  
  .. code-block:: bash

     singularity run /oak/stanford/groups/smhsiang/aerialhist/stitching/containers/surf_ceres.sif \
         python3 /home/users/sidsur/aerial-history-stitching/main.py \
         --config /oak/stanford/groups/smhsiang/aerialhist/stitching/config/Gambia/gambia_53.yml \
         --stage initialize-graph

- Submit:

  .. code-block:: bash

     sbatch slurm_init_graph.sh

6. Optimize Links Stage
-------------------------
Collect and cache links for joint optimization (here cluster 0).

6.1 Prepare SLURM Script

.. code-block:: bash

   cp slurm_init_graph.sh slurm_opt_links.sh

- In **slurm_opt_links.sh**:
  
  .. code-block:: text

     #SBATCH -p dev
     #SBATCH -c 1
  
  .. code-block:: bash

     singularity run /oak/stanford/groups/smhsiang/aerialhist/stitching/containers/surf_ceres.sif \
         python3 /home/users/sidsur/aerial-history-stitching/main.py \
         --config /oak/stanford/groups/smhsiang/aerialhist/stitching/config/Gambia/gambia_53.yml \
         --stage optimize-links \
         --ids 0              # or “--topn 1” for largest cluster

- Submit:

  .. code-block:: bash

     sbatch slurm_opt_links.sh

7. Ceres-Opt Stage
--------------------
Run joint optimization of camera positions.

7.1 Prepare SLURM Script

.. code-block:: bash

   cp slurm_opt_links.sh slurm_ceres_opt.sh

- In **slurm_ceres_opt.sh**:
  
  .. code-block:: text

     #SBATCH -p serc,normal
     #SBATCH -c 30
  
  .. code-block:: bash

     singularity run /oak/stanford/groups/smhsiang/aerialhist/stitching/containers/surf_ceres.sif \
         python3 /home/users/sidsur/aerial-history-stitching/main.py \
         --config /oak/stanford/groups/smhsiang/aerialhist/stitching/config/Gambia/gambia_53.yml \
         --stage ceres-opt \
         --ids 0

- Submit:

  .. code-block:: bash

     sbatch slurm_ceres_opt.sh

8. Generate GeoTIFF Stage
--------------------------
Build a quick mosaic to inspect.

8.1 Prepare SLURM Script

.. code-block:: bash

   cp slurm_ceres_opt.sh slurm_geotiff.sh

- In **slurm_geotiff.sh**:
  
  .. code-block:: text

     #SBATCH -p serc,normal
     #SBATCH -c 30
  
  .. code-block:: bash

     singularity run /oak/stanford/groups/smhsiang/aerialhist/stitching/containers/surf_ceres.sif \
         python3 /home/users/sidsur/aerial-history-stitching/main.py \
         --config /oak/stanford/groups/smhsiang/aerialhist/stitching/config/Gambia/gambia_53.yml \
         --stage generate-geotiff \
         --output-gsd 10      # 10 m/pixel for quick preview

- Submit:

  .. code-block:: bash

     sbatch slurm_geotiff.sh

9. Constrained Optimization Stage
----------------------------------
Refine with ground control points (GCP).

9.1 Update Config

.. code-block:: yaml

   # At bottom of gambia_53.yml
   gcp_file: /path/to/Gambia/Gambia_gcp_points.csv

9.2 Prepare SLURM Script

.. code-block:: bash

   cp slurm_geotiff.sh slurm_constrained_opt.sh

- In **slurm_constrained_opt.sh**:
  
  .. code-block:: text

     #SBATCH -p serc,normal
     #SBATCH -c 30
  
  .. code-block:: bash

     singularity run /oak/stanford/groups/smhsiang/aerialhist/stitching/containers/surf_ceres.sif \
         python3 /home/users/sidsur/aerial-history-stitching/main.py \
         --config /oak/stanford/groups/smhsiang/aerialhist/stitching/config/Gambia/gambia_53.yml \
         --stage constrained-opt \
         --ids 0

- Submit:

  .. code-block:: bash

     sbatch slurm_constrained_opt.sh

10. High-Resolution Mosaic Generation
-------------------------------------
Produce the final, fine-scale raster (1 m/pixel).

10.1 Prepare SLURM Script

.. code-block:: bash

   cp slurm_constrained_opt.sh slurm_final_geotiff.sh

- In **slurm_final_geotiff.sh**:
  
  .. code-block:: text

     #SBATCH -p serc,normal
     #SBATCH -c 30
  
  .. code-block:: bash

     singularity run /oak/stanford/groups/smhsiang/aerialhist/stitching/containers/surf_ceres.sif \
         python3 /home/users/sidsur/aerial-history-stitching/main.py \
         --config /oak/stanford/groups/smhsiang/aerialhist/stitching/config/Gambia/gambia_53.yml \
         --stage generate-geotiff \
         --output-gsd 1       # 1 m/pixel high-res

- Submit:

  .. code-block:: bash

     sbatch slurm_final_geotiff.sh

11. Inspect Final Mosaic in Jupyter
-----------------------------------
Open your notebook and plot the new GeoTIFF:

.. code-block:: python

   import rasterio
   import matplotlib.pyplot as plt

   with rasterio.open('/oak/.../results/Gambia/gambia_53/mosaic_1m.tif') as src:
       fig, ax = plt.subplots()
       ax.imshow(src.read(1))
       ax.set_title('Gambia Mosaic @ 1 m/pixel')
       plt.show()
```