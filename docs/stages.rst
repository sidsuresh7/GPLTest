Stage-by-Stage Reference
========================

Below is a concise version of the internal “Stitching Pipeline Workflow”
document :contentReference[oaicite:0]{index=0}:contentReference[oaicite:1]{index=1}.  Each subsection shows:

* **Command** – minimal CLI invocation.
* **Main outputs** – new or modified artefacts.
* **Common failure points** – what to check when the stage errors.

Initialize
----------
*Command*

.. code-block:: bash

   python main.py --config <CFG> --stage initialize

*Outputs*  `img_df.geojson` (one row / image).  
*Failures*  Bad paths ⇒ empty dataframe.

Crop
----
.. code-block:: bash

   python main.py --config <CFG> --stage crop

Populates `cropping_mask`.  
If masks look wrong, tweak `margin_*` in YAML and rerun.

Inspect cropping
----------------
Quick diagnostic:

.. code-block:: bash

   python main.py --config <CFG> --stage inspect-cropping

Generates sample overlays in `cropping_inspection/`.

Featurize
---------
SURF key-points to HDF5.

Swath-breaks
------------
Detects links between consecutive images; sets `swath_id` & `geometry`.

Initialize-from-plots
---------------------
Uses sortie plots to seed `cluster_id = -2`.  
**dev** partition is enough.

New-neighbors
-------------
Adds cross-swath links (10 nearest neighbors per image).

Initialize-graph
----------------
Connected-component detection; assigns real cluster IDs.

Opt-links → Ceres-opt / Constrained-opt
---------------------------------------
Collect high-quality links then run global (or constrained) bundle
adjustment.  Watch `optim_inclusion_threshold`.

Generate-geotiffs
-----------------
Reprojects each cluster; choose `--output-gsd` based on `estimate-gsd`.

COG creation & upload
---------------------
Not pipeline stages; run the `rio merge` / `rio cogeo` loops then push to the
Google Cloud bucket, authenticate with `gcloud`.

GCP collection flow
-------------------
See PDF for conditional paths when gathering or refining ground-control
points.

*Tip*: After any optimisation stage, always inspect `links_df.p` size to catch
silent link-filtering bugs.


