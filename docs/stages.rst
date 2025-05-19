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
  - Update `img_cache_folder` to your cache path for Gambia/gambia_53.
  - Update `checkpoint_cache_folder` and `raster_output_folder` similarly.

3. Run the Initialize Stage
----------------------------
The initialize stage scans folders, extracts SURF features, and builds `img_df.geojson`.

3.1 Prepare a SLURM Script

.. code-block:: bash

   cp slurm_initialize_example.sh my_initialize.sh

- Edit **my_initialize.sh** to include:

  .. code-block:: bash

     singularity run /oak/stanford/groups/smhsiang/aerialhist/stitching/containers/surf_ceres.sif \
         python3 /home/users/sidsur/aerial-history-stitching/main.py \
         --config /oak/stanford/groups/smhsiang/aerialhist/stitching/config/Gambia/gambia_53.yml \
         --stage initialize

- Submit the job:

  .. code-block:: bash

     sbatch my_initialize.sh

4. Inspect Results in Jupyter
-----------------------------
Once the job completes, check your outputs in a notebook:

.. code-block:: python

   import os
   import geopandas as gpd

   # Path to the configuration’s output folder
   cache_dir = '/oak/stanford/groups/smhsiang/aerialhist/stitching/results/Gambia/gambia_53'

   # Full path to the geojson cache file
   cache_file = os.path.join(cache_dir, 'img_df.geojson')

   # Read the geojson into a GeoDataFrame
   img_df = gpd.read_file(cache_file)

   # Display the GeoDataFrame
   img_df

5. Expected Output
------------------
- A file named **img_df.geojson** in your `results/Gambia/gambia_53` folder.
- It should contain one row per image, with geometry for each camera location.

6. Crop Stage
-------------
This stage computes per–image cropping masks and (optionally) generates inspection files.

6.1 Adjust Cropping Parameters (Optional)

Modify these values in your YAML config if you need different margins:

.. code-block:: yaml

   # Example cropping margins (values in pixels)
   margin_bottom: 50
   margin_left:   50
   margin_top:    50
   margin_right:  50

6.2 Run the Crop Stage

.. code-block:: bash

   cp slurm_initialize.sh slurm_crop.sh

- Edit **slurm_crop.sh**:
  - Add a CPU-allocation directive:

    .. code-block:: text

       #SBATCH -c 30

  - Replace the stage command with:

    .. code-block:: bash

       singularity run /oak/stanford/groups/smhsiang/aerialhist/stitching/containers/surf_ceres.sif \
           python3 /home/users/sidsur/aerial-history-stitching/main.py \
           --config /oak/stanford/groups/smhsiang/aerialhist/stitching/config/Gambia/gambia_53.yml \
           --stage crop

- Submit the job:

  .. code-block:: bash

     sbatch slurm_crop.sh

**Output:** Updates `img_df.geojson`, adding a new `cropping_mask` column for every image.

6.3 Inspect Cropping Masks (Test Run)
-------------------------------------
Before running the full crop, generate inspection files for a small subset:

.. code-block:: bash

   singularity run /oak/stanford/groups/smhsiang/aerialhist/stitching/containers/surf_ceres.sif \
       python3 /home/users/sidsur/aerial-history-stitching/main.py \
       --config /oak/stanford/groups/smhsiang/aerialhist/stitching/config/Gambia/gambia_53.yml \
       --stage crop \
       --test-crop

- Submit the test job:

  .. code-block:: bash

     sbatch slurm_crop.sh

Inspection files appear in:

.. code-block:: text

   /oak/stanford/groups/smhsiang/aerialhist/stitching/results/Gambia/gambia_53/cropping_inspection/

They contain sample masks for margin verification and do not modify `img_df.geojson`.

7. Featurization Stage
----------------------
This stage extracts SURF features from each image and writes them to HDF5 files.

7.1 Copy Your SLURM Script

.. code-block:: bash

   cp slurm_crop.sh slurm_featurize.sh

7.2 Edit the Script for Featurization

- In **slurm_featurize.sh**, keep any SBATCH directives and replace the command with:

  .. code-block:: bash

     singularity run /oak/stanford/groups/smhsiang/aerialhist/stitching/containers/surf_ceres.sif \
         python3 /home/users/sidsur/aerial-history-stitching/main.py \
         --config /oak/stanford/groups/smhsiang/aerialhist/stitching/config/Gambia/gambia_53.yml \
         --stage featurize

7.3 Submit the Job

.. code-block:: bash

   sbatch slurm_featurize.sh

**Output:** In your `img_cache_folder`, you will find one `.hdf5` file per image containing extracted SURF descriptors.

8. Swath-Breaks Stage
---------------------
This stage links images into flight “swaths” and updates your image catalog.

8.1 Copy Your SLURM Script

.. code-block:: bash

   cp slurm_crop.sh slurm_swath_breaks.sh

8.2 Edit for Swath-Breaks

- In **slurm_swath_breaks.sh**, replace the pipeline command with:

  .. code-block:: bash

     singularity run /oak/stanford/groups
