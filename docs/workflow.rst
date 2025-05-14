.. contents::
   :local:
   :depth: 2

=============================
Aerial-Image Stitching Guide
=============================

This step-by-step walkthrough uses **colorful admonitions** to distinguish constant values, editable fields, and important notes. Simply copy-and-paste into your Sphinx/ReadTheDocs project.

.. raw:: html

   <style>
     /* Customize admonition headers */
     .admonition.note .admonition-title { background-color: #4A90E2; color: white; }
     .admonition.tip .admonition-title  { background-color: #7ED321; color: white; }
     .admonition.important .admonition-title { background-color: #F5A623; color: white; }
     .admonition.warning .admonition-title { background-color: #D0021B; color: white; }
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

         digitized_plot: /oak/.../datasets/scan_lines/Gambia/Gambia_scan_lines.csv


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


--------------------------
**General SLURM Tips**
--------------------------

- **Keep constant**: module loads, Singularity container commands.  
- **Always edit**:
  - `--config` path  
  - `--stage` name  
  - Stage-specific flags (e.g. `--ids`)  
  - `#SBATCH` CPUs or partition  
