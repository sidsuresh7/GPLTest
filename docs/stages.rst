.. contents::
   :local:
   :depth: 2

=============================
User Step By Step Guide
=============================

1. Inspect the Dataset Spreadsheet
----------------------------------
- Open the “DataSet” spreadsheet.
- Each row is one ground survey (a British government plot).
- The “Sorted plots” tab shows the flight trajectory over each plot.

2. Create a Configuration File
------------------------------
A YAML file tells the pipeline:
- Where to find raw images.
- Where to save caches and final outputs.

2.1 Example Paths

.. code-block:: yaml

   img_cache_folder: /scratch/groups/smhsiang/ahp/stitching/cache/Zambia/c82e/SURF
   checkpoint_cache_folder: /oak/stanford/groups/smhsiang/aerialhist/stitching/results/Zambia/c82e
   raster_output_folder: /oak/stanford/groups/smhsiang/aerialhist/stitching/results/Zambia/c82e

2.2 Create your config

.. code-block:: bash

   find ~+ -type d -name "NCAP_DOS_53_GA*" | sort
   cp gambia_124.yml gambia_53.yml

- In **gambia_53.yml**:
  - Update the three folders above.
  - Add at the bottom:

    .. code-block:: yaml

       digitized_plot: /oak/stanford/groups/smhsiang/aerialhist/datasets/scan_lines/Gambia/Gambia_scan_lines.csv

- **Submit job**

- **Expected output:**
  - A new file `gambia_53.yml` containing your updated paths and `digitized_plot`.

3. Sorted Plots Stage
---------------------
Use the DOS_PLOTS data to seed the pipeline.

3.1 Update config

.. code-block:: yaml

   # at the bottom of gambia_53.yml
   digitized_plot: /oak/stanford/groups/smhsiang/aerialhist/datasets/DOS_PLOTS/Gambia

3.2 Prepare SLURM script

.. code-block:: bash

   cp slurm_initialize.sh slurm_sorted_plots.sh

- In **slurm_sorted_plots.sh**:
  - Change partition to `dev`.
  - Remove any `#SBATCH -c` line.
  - Change stage to `initialize-from-plots`.

- **Submit job**

- **Expected output:**
  - An updated `img_df.geojson` in your results folder.
  - Empty `.out` and `.err` logs (no errors or warnings).

4. New Neighbors Stage
----------------------
Compute links within each cluster (here, the two largest).

4.1 Prepare SLURM script

.. code-block:: bash

   cp slurm_crop.sh slurm_new_neighbors.sh

- In **slurm_new_neighbors.sh**:
  - Partition: `serc,normal`
  - CPUs: `-c 30`
  - Stage: `new-neighbors`
  - IDs: `-2`  (top two clusters)

- **Submit job**

- **Expected output:**
  - Link files (e.g. `neighbors_cluster_<id>.json`) for each of the two clusters.

5. Initialize Graph Stage
--------------------------
Build connected components from your links.

5.1 Prepare SLURM script

.. code-block:: bash

   cp slurm_crop.sh slurm_init_graph.sh

- In **slurm_init_graph.sh**:
  - Partition: `dev`
  - CPUs: `-c 1`
  - Stage: `initialize-graph`

- **Submit job**

- **Expected output:**
  - `img_df.geojson` updated with:
    - `cluster_id` for each image (≥ 0 or –1)
    - `global_trans` and `geometry` fields

6. Optimize Links Stage
-----------------------
Gather and cache links for joint optimization (cluster 0).

6.1 Prepare SLURM script

.. code-block:: bash

   cp slurm_init_graph.sh slurm_opt_links.sh

- In **slurm_opt_links.sh**:
  - Partition: `dev`
  - CPUs: `-c 1`
  - Stage: `optimize-links`
  - IDs: `0`  (or `--topn 1`)

- **Submit job**

- **Expected output:**
  - A cache file like `optimize_links_cluster_0.pickle` in your results folder.

7. Ceres-Opt Stage
------------------
Run the joint optimization.

7.1 Prepare SLURM script

.. code-block:: bash

   cp slurm_opt_links.sh slurm_ceres_opt.sh

- In **slurm_ceres_opt.sh**:
  - Partition: `serc,normal`
  - CPUs: `-c 30`
  - Stage: `ceres-opt`
  - IDs: `0`

- **Submit job**

- **Expected output:**
  - Optimized parameters file, e.g. `ceres_opt_results_cluster_0.json`.

8. Generate GeoTIFF Stage
-------------------------
Create a quick preview mosaic.

8.1 Prepare SLURM script

.. code-block:: bash

   cp slurm_ceres_opt.sh slurm_geotiff.sh

- In **slurm_geotiff.sh**:
  - Partition: `serc,normal`
  - CPUs: `-c 30`
  - Stage: `generate-geotiff`
  - `--output-gsd 10`  (10 m/pixel)

- **Submit job**

- **Expected output:**
  - A preview GeoTIFF (e.g. `mosaic_10m.tif`) in your results folder.

9. Constrained Optimization Stage
---------------------------------
Refine with ground control points (GCP).

9.1 Update config

.. code-block:: yaml

   # at the bottom of gambia_53.yml
   gcp_file: /path/to/Gambia/Gambia_gcp_points.csv

9.2 Prepare SLURM script

.. code-block:: bash

   cp slurm_geotiff.sh slurm_constrained_opt.sh

- In **slurm_constrained_opt.sh**:
  - Partition: `serc,normal`
  - CPUs: `-c 30`
  - Stage: `constrained-opt`
  - IDs: `0`

- **Submit job**

- **Expected output:**
  - A new optimized parameters file with GCPs applied, e.g. `ceres_opt_gcp_cluster_0.json`.

10. High-Resolution Mosaic Generation
-------------------------------------
Produce the final 1 m/pixel mosaic.

10.1 Prepare SLURM script

.. code-block:: bash

   cp slurm_constrained_opt.sh slurm_final_geotiff.sh

- In **slurm_final_geotiff.sh**:
  - Partition: `serc,normal`
  - CPUs: `-c 30`
  - Stage: `generate-geotiff`
  - `--output-gsd 1`  (1 m/pixel)

- **Submit job**

- **Expected output:**
  - High-resolution GeoTIFF `mosaic_1m.tif` in your results folder.

11. Inspect Final Mosaic in Jupyter
-----------------------------------
Open your notebook and plot the 1 m raster:

.. code-block:: python

   import rasterio
   import matplotlib.pyplot as plt

   with rasterio.open('/oak/.../results/Gambia/gambia_53/mosaic_1m.tif') as src:
       fig, ax = plt.subplots()
       ax.imshow(src.read(1))
       ax.set_title('Gambia Mosaic @ 1 m/pixel')
       plt.show()
