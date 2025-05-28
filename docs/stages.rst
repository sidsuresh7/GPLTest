.. contents::
\:local:
\:depth: 2

\=============================
User Step By Step Guide
=======================

1. Inspect the Dataset Spreadsheet

---

* Open the “DataSet” spreadsheet.
* Understand that each row represents one ground survey (a plot of land the British government surveyed).
* Note that the “Sorted plots” tab shows maps with the plane’s flight trajectory overlaid on each plot.

2. Create a Configuration File

---

A configuration (YAML) file tells the pipeline:

* Where to find the raw images.
* Where to save intermediate caches and final outputs.

2.1 Example Paths

.. code-block:: yaml

# Path to store downloaded/cached image features

img\_cache\_folder: /scratch/groups/smhsiang/ahp/stitching/cache/Zambia/c82e/SURF

# Path to store intermediate checkpoints

checkpoint\_cache\_folder: /oak/stanford/groups/smhsiang/aerialhist/stitching/results/Zambia/c82e

# Path to write the final stitched raster output

raster\_output\_folder: /oak/stanford/groups/smhsiang/aerialhist/stitching/results/Zambia/c82e

2.2 Create Your New Config

.. code-block:: bash

find \~+ -type d -name "NCAP\_DOS\_53\_GA\*" | sort
cp gambia\_124.yml gambia\_53.yml

* Edit **gambia\_53.yml**:

  * Update `img_cache_folder` to your cache path for Gambia/gambia\_53.
  * Update `checkpoint_cache_folder` and `raster_output_folder` similarly.

3. Sorted Plots Stage

---

This stage copies downloaded DOS plots into the pipeline and updates the config.

3.1 Update YAML Config

.. code-block:: yaml

# Add at the bottom of your existing config file:

digitized\_plot: /oak/stanford/groups/smhsiang/aerialhist/datasets/scan\_lines/Gambia/Gambia\_scan\_lines.csv

3.2 Prepare SLURM Script

.. code-block:: bash

cp slurm\_initialize\_example.sh slurm\_sorted\_plots.sh

* In **slurm\_sorted\_plots.sh**:

  * Change the stage flag: `--stage initialize-from-plots`
  * Change partition: `#SBATCH -p dev`
  * Remove any `#SBATCH -c` or CPU directives (defaults to 1 CPU).

3.3 Submit the Job

.. code-block:: bash

sbatch slurm\_sorted\_plots.sh

* After completion, confirm that `.err` and `.out` files are empty.

4. New Neighbors Stage

---

This stage calculates links within clusters.

4.1 Prepare SLURM Script

.. code-block:: bash

cp slurm\_crop.sh slurm\_new\_neighbors.sh

* In **slurm\_new\_neighbors.sh**:

  * Change stage and IDs: `--stage new-neighbors --ids -2`
  * Set partition and CPU count:
    `#SBATCH -p serc,normal`
    `#SBATCH -c 30`

4.2 Submit the Job

.. code-block:: bash

sbatch slurm\_new\_neighbors.sh

5. Initialize Graph Stage

---

Reconstruct the mosaic components using collected links.

5.1 Prepare SLURM Script

.. code-block:: bash

cp slurm\_crop.sh slurm\_init\_graph.sh

* In **slurm\_init\_graph.sh**:

  * Change partition: `#SBATCH -p dev`
  * Set CPU count to 1 (`#SBATCH -c 1`)
  * Stage flag: `--stage initialize-graph`

5.2 Submit the Job

.. code-block:: bash

sbatch slurm\_init\_graph.sh

* **Output**:

  * `img_df.geojson` updated with `cluster_id`, `global_trans`, and `geometry`.
  * Logs show cluster sizes.
  * Note: axes may flip compared to Jupyter plots.

6. Optimize Links Stage

---

Precompute link sets and save for optimization.

6.1 Prepare SLURM Script

.. code-block:: bash

cp slurm\_init\_graph.sh slurm\_optimize\_links.sh

* In **slurm\_optimize\_links.sh**:

  * Change stage and IDs: `--stage optimize-links --ids 0`
  * Partition: `#SBATCH -p dev`
  * CPU count to 1 (`#SBATCH -c 1`)

6.2 Submit the Job

.. code-block:: bash

sbatch slurm\_optimize\_links.sh

* Creates a file listing links for cluster 0.

7. Ceres-Opt Stage

---

Jointly optimize positions via Ceres Solver.

7.1 Prepare SLURM Script

.. code-block:: bash

cp slurm\_optimize\_links.sh slurm\_ceres\_opt.sh

* In **slurm\_ceres\_opt.sh**:

  * Stage flag: `--stage ceres-opt`
  * Partition: `#SBATCH -p serc,normal`
  * CPU count: `#SBATCH -c 30`
  * IDs: `--ids 0`

7.2 Submit the Job

.. code-block:: bash

sbatch slurm\_ceres\_opt.sh

8. Generate GeoTIFF Stage

---

Create a quick mosaic for inspection.

8.1 Prepare SLURM Script

.. code-block:: bash

cp slurm\_ceres\_opt.sh slurm\_generate\_tiff.sh

* In **slurm\_generate\_tiff.sh**:

  * Stage flag: `--stage generate-geotiff`
  * Set output GSD in YAML or via `--output-gsd 1`
  * Partition: `#SBATCH -p serc,normal`
  * CPU count: `#SBATCH -c 30`

8.2 Submit the Job

.. code-block:: bash

sbatch slurm\_generate\_tiff.sh

* **Output**: a mosaic in GeoTIFF form. Use `output-gsd: 1` for 1m resolution.

9. Constrained Optimization Stage

---

Refine mosaic using Ground Control Points (GCPs).

9.1 Update Config

.. code-block:: yaml

# At the bottom of your config:

gcp\_file: /path/to/your/Gambia\_GCP\_points.csv

9.2 Prepare SLURM Script

.. code-block:: bash

cp slurm\_generate\_tiff.sh slurm\_constrained\_opt.sh

* In **slurm\_constrained\_opt.sh**:

  * Stage flag: `--stage constrained-opt`
  * Partition & CPU: `#SBATCH -p serc,normal`, `#SBATCH -c 30`

9.3 Submit the Job

.. code-block:: bash

sbatch slurm\_constrained\_opt.sh

10. Jupyter Notebook Inspection

---

Open your notebook and plot the updated geometry:

.. code-block:: python

import geopandas as gpd
import matplotlib.pyplot as plt

img\_df = gpd.read\_file('/oak/stanford/groups/smhsiang/aerialhist/stitching/results/Gambia/gambia\_53/img\_df.geojson')
img\_df.plot()
plt.show()

11. Task: Create High-Resolution Raster

---

Use the latest mosaic and generate a 1m-resolution GeoTIFF for upload.

.. code-block:: bash

# Ensure your config has:

output\_gsd: 1

sbatch slurm\_generate\_tiff.sh

* **Note**: Higher resolution increases storage; 1m per pixel gives fine detail.
