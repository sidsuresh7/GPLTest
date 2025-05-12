Quick-start Workflow
====================

Step 1  – Create a config
-------------------------
Copy the template and edit *only* the paths and margins:

.. code-block:: bash

   cp config/template.yml config/gambia_53.yml
   # open the new file in VS Code
   # change:
   #   raw_images_folder, img_cache_folder,
   #   raster_output_folder, checkpoint_cache_folder
   #   margin_* values if the frame is thick or thin

Step 2  – Run **initialize**
----------------------------
From the repo root:

.. code-block:: bash

   singularity run containers/surf_ceres.sif \
       python main.py \
       --config config/gambia_53.yml \
       --stage initialize

✓  Creates `img_df.geojson` (one row per image) :contentReference[oaicite:0]{index=0}:contentReference[oaicite:1]{index=1}.

Step 3  – Crop & inspect
------------------------
1. Submit a Slurm job (heavy parallel IO):

   .. code-block:: bash

      # crop.slurm
      #SBATCH -c 30
      #SBATCH -p serc,normal
      singularity exec surf_ceres.sif \
          python main.py --config $CFG --stage crop

2. Verify interactively:

   .. code-block:: bash

      python main.py --config $CFG --stage inspect-cropping
      # opens sample images with the mask overlay :contentReference[oaicite:2]{index=2}:contentReference[oaicite:3]{index=3}

   *Too tight / too loose?* Adjust `margin_*` in the YAML and re-run **crop**.

Step 4  – Featurize
-------------------
Compute SURF key-points (cached to disk):

.. code-block:: bash

   sbatch -c 30 featurize.slurm   # same pattern, just change --stage

**Pro-tip**: set `surf_workers = 6` so that `surf_workers*5 ≈ CPUs` :contentReference[oaicite:4]{index=4}:contentReference[oaicite:5]{index=5}.

Step 5  – Swath breaks
----------------------
Detect “next-frame” links:

.. code-block:: bash

   sbatch -c 30 swath_breaks.slurm   # --stage swath-breaks

Tweak `swath_break_threshold` if you see false links or missed joins.

Step 6  – (Optionally) initialize from sortie plots
---------------------------------------------------
Add one line to the YAML:

.. code-block:: yaml

   digitized_plot: /oak/.../scan_lines/Gambia/Gambia_scan_lines.csv

Then run on the lightweight **dev** partition:

.. code-block:: bash

   sbatch -p dev init_from_plots.slurm   # --stage initialize-from-plots

Step 7  – Grow the graph & optimise
-----------------------------------
A typical sequence for the biggest 10 clusters:

.. code-block:: bash

   # still on dev; quick operations
   python main.py --config $CFG --stage initialize-graph

   # back on 30 CPUs
   python main.py --config $CFG --stage new-neighbors --ids top10
   python main.py --config $CFG --stage opt-links      --ids top10
   python main.py --config $CFG --stage ceres-opt      --ids top10

Step 8  – Raster & publish
--------------------------
.. code-block:: bash

   python main.py --config $CFG --stage create-raster --raster-type clusters \
                  --ids top10 --alpha-mode overlay --annotate graph

   # Inspect, then generate final GeoTIFFs
   python main.py --config $CFG --stage generate-geotiffs --ids top10

   # Convert to COG & push to GCP bucket (requires rasterio+gcloud)
   ml python/3.9 google-cloud-sdk
   rio cogeo create ...               # see stages page for full loop
   gcloud storage cp *.tif gs://gee_assets/...

That’s it! For anything trickier—manual links, GCP workflows—see
:doc:`stages`.

