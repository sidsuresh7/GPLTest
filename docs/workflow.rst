End‑to‑End Workflow (Narrated Walk‑through)
==========================================

This chapter knits together every stage into a **storyboard** you can follow
on your first real‑world contract.  Each section gives:

* **Goal** – why the stage exists.
* **One‑liner** – minimal command (Docker/Singularity‑agnostic).
* **Expected artefacts** – filenames and where to find them.
* **Troubleshooting** – what can go wrong and how to fix.
* **Time & resources** – empirical runtime on Sherlock for 1 swath ≈ 1 GB.

We take *Gambia 53* as the concrete example.

Step 0  |  Project skeleton
--------------------------

.. code-block:: bash

   aerial-history-stitching/
   ├── configs/              # YAMLs live here
   │   └── gambia_53.yml
   ├── jobs/                 # Slurm scripts grouped by stage
   ├── notebooks/
   ├── src/ (or main.py)
   └── docs/

Commit early – even empty placeholders help reviewers track progress.

Step 1  |  Initialise state ledger
---------------------------------
*Goal.* Enumerate every TIFF/JPEG in the contract, capture metadata (film, frame
number, scanner resolution) and persist in a **GeoPandas** dataframe –
`img_df.geojson`.

.. code-block:: bash

   python main.py --config configs/gambia_53.yml --stage initialize

Expected artefacts
~~~~~~~~~~~~~~~~~~
* `img_df.geojson` (few MB) in `raster_output_folder`.
* `initialize.log` in `checkpoint_cache_folder`.

Troubleshooting
~~~~~~~~~~~~~~~
**Symptom:** *img_df.geojson is empty* → paths wrong in YAML.

**Symptom:** *UnicodeDecodeError* → corrupted filename; run
`rename 's/[^[:print:]]/_/g' *.jpg` in the raw folder.

Time & resources
~~~~~~~~~~~~~~~~
CPU‑bound on metadata I/O – 2 min on dev partition with 1 CPU.

Step 2  |  Crop background & annotate
------------------------------------
*Goal.* Remove scanner bed, film frame & handwritten scribbles; output per‑image
bounds and global frame mask.

.. code-block:: bash

   # heavy parallel I/O
   sbatch jobs/gambia_crop.slurm

Slurm snippet:

.. literalinclude:: ../../jobs/gambia_crop.slurm
   :language: bash
   :lines: 1-15

Artefacts & QC
~~~~~~~~~~~~~~
* `bounds_xmin/xmax/ymin/ymax` columns in `img_df`.
* Mask previews in `cropping_inspection/` – browse with `feh` or Jupyter.

Pitfalls & fixes
~~~~~~~~~~~~~~~~
*Black bars remain* → lower `cropping_std_threshold` or increase
`cropping_filter_sigma`.

*Edge of photo chopped off* → reduce `margin_*`.

Runtime: 30 CPUs, ≈ 0.2 s per 40 MP photo ⇒ ~10 minutes for 3,000 images.

Step 3  |  Featurize (SURF descriptors)
---------------------------------------
*Goal.* Pre‑compute keypoints so later stages never touch raw images again.

.. code-block:: bash

   sbatch jobs/gambia_featurize.slurm

Outputs
~~~~~~~
* One HDF5 file per image inside `img_cache_folder` (≈ 80 kB each).

Tips
~~~~
* Monitor progress with `watch -n5 "ls -1 img_cache_folder | wc -l"`.
* If your node runs out of RAM, shrink `surf_workers`.

Runtime: 30 CPUs, 3 hours for 3,000 images @ 400 keypoints each.

Step 4  |  Swath inference (adjacent images)
-------------------------------------------
*Goal.* Segment film roll into continuous flight lines (“swaths”).

.. code-block:: bash

   sbatch jobs/gambia_swath_breaks.slurm

Outputs
~~~~~~~
* `links_df.p` – DataFrame of all consecutive links; bad links contain NaNs.
* `img_df.swath_id` column populated.

Diagnosing bad thresholds
~~~~~~~~~~~~~~~~~~~~~~~~~
#. Load `links_df.p` in a notebook.
#. Plot histogram of `inliers`.
#. Pick a cut‑off just before the long‑tail.

Runtime: linear in number of frames; 30 CPUs, ~40 min for 3,000 pairs.

Step 5  |  (Optional) Position from sortie plots
-----------------------------------------------
*Goal.* Rough‑place each swath in map space using digitised endpoints.

.. code-block:: bash

   sbatch -p dev jobs/gambia_init_plots.slurm

Right after completion you can run

.. code-block:: bash

   python viz/plot_clusters.py --config $CFG --show -2   # cluster ‑2 preview

Step 6  |  Initial graph & neighbour links
-----------------------------------------
*Goal.* Turn pairwise links into a directed forest; compute extra links within
and across swaths to strengthen graph connectivity.

.. code-block:: bash

   python main.py --config $CFG --stage initialize-graph
   python main.py --config $CFG --stage new-neighbors --ids top10 --n-neighbors 10

Heuristics
~~~~~~~~~~
* Set `n-neighbors` near 10 to avoid O(N²) explosion while still giving the
  optimiser enough constraints.
* Watch console: “cluster 42 → 1,240 nodes, density 0.018”.  Anything under
  0.005 may optimise poorly – rerun `new-neighbors` with a larger N.

Step 7  |  Graph densification & optimisation
-------------------------------------------
*Goal.* Select high‑quality links (`opt-links`), then non‑linear least‑squares
fit (`ceres-opt` or `global-opt`).

.. code-block:: bash

   python main.py --config $CFG --stage opt-links --ids top10
   python main.py --config $CFG --stage ceres-opt --ids top10

Diagnostics
~~~~~~~~~~~
* `optim_report.csv` – per‑iteration RMSE of x, y, θ, scale.
* Convergence plateau?  Increase `n_iter` or reduce `optim_lr_*`.

Runtime per 1k images: 30 CPUs, 20 min (Ceres) or 1 GPU, 8 min (global‑opt).

Step 8  |  Rasterisation & Cloud Optimised GeoTIFFs
--------------------------------------------------
*Goal.* Produce a visually inspectable mosaic, then convert to streaming‑friendly COGs.

.. code-block:: bash

   python main.py --config $CFG --stage create-raster --raster-type clusters \
                  --ids top10 --alpha-mode blend --annotate graph
   python main.py --config $CFG --stage generate-geotiffs --ids top10 --output-gsd 1

Post‑processing
~~~~~~~~~~~~~~~
.. code-block:: bash

   for tif in results/*cluster*_gsd1.tif; do
       rio cogeo create "$tif" "${tif%.tif}_cog.tif" --overview-level 2
       gcloud storage cp "${tif%.tif}_cog.tif" gs://gee_assets/gambia53/
   done

Index the new files in Google Earth Engine using the helper notebook
`notebooks/create_cog_backed_assets.ipynb`.

Congratulations – your contract is live!

Appendix |  Typical Timings Summary
-----------------------------------
========================================  ============  ============
Stage                                     3,000 photos  10,000 photos
========================================  ============  ============
initialize                                2 min         7 min
crop + inspect                            15 min        40 min
featurize                                 3 h           10 h
swath-breaks                              40 min        2 h
new-neighbors (n=10)                      35 min        2 h
ceres-opt (30 CPU)                        20 min        1 h
create-raster (blend)                     25 min        1½ h
COG conversion                            8 min         25 min
========================================  ============  ============