.. contents::
   :local:
   :depth: 2

=============================
User Step By Step Guide
=============================

This step-by-step walkthrough uses **colorful admonitions** to distinguish constant values, editable fields, and important notes. Simply copy-and-paste into your Sphinx/ReadTheDocs project.

.. raw:: html

   <style>
     /* Customize admonition headers */
     .admonition.note .admonition-title { background-color:rgb(157, 194, 236); color: white; }
     .admonition.tip .admonition-title  { background-color:rgb(204, 238, 169); color: white; }
     .admonition.important .admonition-title { background-color: #F5A623; color: white; }
     .admonition.warning .admonition-title { background-color:rgb(234, 162, 170); color: white; }
   </style>

1. Create & Configure Your `.yml` File
=======================================

.. admonition:: What stays constant
   :class: note

   - The **structure** and **key names** in any `*.yml` config (e.g. `gambia_124.yml`).

.. admonition:: What to edit
   :class: tip

   1. **Copy template**  
      .. code-block:: bash

         cp gambia_124.yml gambia_53.yml

   2. **Update folder paths** under these keys:

      .. code-block:: yaml

         img_cache_folder:        /scratch/.../cache/Gambia/gambia_53/SURF
         checkpoint_cache_folder: /oak/.../results/Gambia/gambia_53
         raster_output_folder:    /oak/.../results/Gambia/gambia_53

   3. **Add digitized-plot** (required for sortie plots):

      .. code-block:: yaml

         digitized_plot: /oak/stanford/groups/smhsiang/aerialhist/datasets/scan_lines/Gambia/Gambia_scan_lines.csv

2. Initialize Stage
===================

.. admonition:: What stays constant
   :class: note

   - **Singularity image:**  
     `/oak/.../containers/surf_ceres.sif`  
   - **Python entry-point:**  
     `/home/users/sidsur/aerial-history-stitching/main.py`

.. admonition:: What to edit
   :class: tip

   - **Config path:**

     .. code-block:: bash

        --config /oak/.../config/Gambia/gambia_53.yml

   - **Stage flag:**  
     ``--stage initialize``

.. code-block:: bash

   singularity run /oak/.../containers/surf_ceres.sif \
       python3 /home/users/sidsur/aerial-history-stitching/main.py \
       --config /oak/.../config/Gambia/gambia_53.yml \
       --stage initialize

.. image:: images/initialize.png
   :alt: Preview of the `img_df` GeoDataFrame after initialization
   :align: center
   :width: 80%

3. Cropping & Inspection
========================

.. admonition:: Config edits
   :class: tip

   - **Keys:**  
     `margin_bottom`, `margin_left`, `margin_top`, `margin_right`  
   - **Edit:** numeric values to refine the crop mask.

.. admonition:: SLURM script edits
   :class: warning

   - **CPUs:** `#SBATCH -c 30`  
   - **Stage:** change between `--stage crop` and `--stage inspect-crop`  
   - **Config path:** your new `.yml`

**Workflow**:

1. Submit cropping:

   .. code-block:: bash

      sbatch crop_gambia_53.slurm

2. Open the **Inspect Crop** notebook in Jupyter (under `raster_output_folder`) to view masks.  
3. Tweak margins in your `.yml`, then rerun:

   .. code-block:: bash

      sbatch inspectcrop_gambia_53.slurm

4. Featurization
================

.. admonition:: What stays constant
   :class: note

   - SURF algorithm  
   - Output: `.hdf5` files in `img_cache_folder`

.. admonition:: What to edit
   :class: tip

   - **Stage:** `--stage featurize`  
   - **Config:** path to your `.yml`  
   - **CPUs:** `#SBATCH -c 30`

.. code-block:: bash

   sbatch featurize_gambia_53.slurm

5. Swath Breaks
===============

.. admonition:: What stays constant
   :class: note

   - Key `inlier_threshold` (already in config)

.. admonition:: What to edit
   :class: tip

   - **Stage:** `--stage swath-break`  
   - **CPUs:** `#SBATCH -c 30`

.. code-block:: bash

   sbatch swathbreak_gambia_53.slurm

6. Sortie Plots
===============

.. admonition:: What stays constant
   :class: note

   - You **must** add `digitized_plot:` in your YAML before running.

.. admonition:: What to edit
   :class: tip

   - **Stage:** `--stage initialize-from-plots`  
   - **Partition:** `#SBATCH -p dev`  
   - **Remove** CPU directive (uses 1 CPU)

.. code-block:: bash

   sbatch plots_gambia_53.slurm

7. New Neighbors
================

.. admonition:: What to edit
   :class: tip

   - **Stage:** `--stage new-neighbors`  
   - **IDs:** `--ids -2`  
   - **Partition:** `#SBATCH -p serc,normal`  
   - **CPUs:** `#SBATCH -c 30`

.. code-block:: bash

   sbatch newneighbors_gambia_53.slurm

8. Initialize Graph
===================

Use collected links to build mosaic components. A lightweight stage suitable for `dev` partition.

.. admonition:: What to edit
   :class: tip

   - **Stage:** `--stage initialize-graph`  
   - **Partition:** `#SBATCH -p dev`  
   - **CPUs:** `#SBATCH -c 1`

.. code-block:: bash

   sbatch initgraph_gambia_53.slurm

9. Optimize Links
=================

Collect and cache link data for optimization. Specify target cluster IDs.

.. admonition:: What to edit
   :class: tip

   - **Stage:** `--stage optimize-links`  
   - **IDs:** `--ids 0` (or `--top 1`)  
   - **Partition:** `#SBATCH -p dev`  
   - **CPUs:** `#SBATCH -c 1`

.. code-block:: bash

   sbatch optlinks_gambia_53.slurm

10. Ceres-Opt
============

Perform joint optimization using Ceres Solver.

.. admonition:: What to edit
   :class: tip

   - **Stage:** `--stage ceres-opt`  
   - **IDs:** `--ids 0`  
   - **Partition:** `#SBATCH -p serc,normal`  
   - **CPUs:** `#SBATCH -c 30`

.. code-block:: bash

   sbatch ceresopt_gambia_53.slurm

11. Generate GeoTIFF
====================

Create mosaic raster for inspection. Adjust output GSD for resolution.

.. admonition:: What to edit
   :class: tip

   - **Stage:** `--stage generate-geotiff`  
   - **Output GSD:** `--output_gsd 1` (meters per pixel)  
   - **Partition:** `#SBATCH -p serc,normal`  
   - **CPUs:** `#SBATCH -c 30`

.. code-block:: bash

   sbatch geotiff_gambia_53.slurm

12. Constrained Optimization
============================

Use GCP file for final georeferencing.

.. admonition:: What to edit
   :class: tip

   - **GCP file:** ensure `gcp_file:` in config points to correct cloud path  
   - **Stage:** `--stage constrained-opt`  
   - **Partition:** `#SBATCH -p serc,normal`  
   - **CPUs:** `#SBATCH -c 30`

.. code-block:: bash

   sbatch constropt_gambia_53.slurm

13. Jupyter Notebook Inspection
==============================

Open the inspection notebook in Jupyter to visualize `img_df.geojson` and mosaic geometry.

14. Final Task: High-Res Mosaic
===============================

To produce the high-resolution raster for upload, rerun the Generate GeoTIFF stage with `--output_gsd 1`.

.. admonition:: Important
   :class: important

   Lower GSD values yield higher resolution but larger file sizes.

.. code-block:: bash

   sbatch geotiff_highres_gambia_53.slurm