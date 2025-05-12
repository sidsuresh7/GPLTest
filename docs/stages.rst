Stage-by-Stage Reference
========================

Notation
--------
`$CFG` = path to your YAML configuration  
`<ids>` = cluster ids, or `topN` where **N** is a number

Initialize
----------
.. code-block:: bash

   python main.py --config $CFG --stage initialize

Creates `img_df.geojson` :contentReference[oaicite:6]{index=6}:contentReference[oaicite:7]{index=7}.

Crop  / inspect-cropping
-----------------------
.. code-block:: bash

   python main.py --config $CFG --stage crop
   python main.py --config $CFG --stage inspect-cropping  # visual QC

Use `--test-crop` for a quick sample run :contentReference[oaicite:8]{index=8}:contentReference[oaicite:9]{index=9}.

Featurize
---------
.. code-block:: bash

   python main.py --config $CFG --stage featurize
   python main.py --config $CFG --stage featurize --only-missing

SURF files go to `img_cache_folder` :contentReference[oaicite:10]{index=10}:contentReference[oaicite:11]{index=11}.

Swath-breaks
------------
.. code-block:: bash

   python main.py --config $CFG --stage swath-breaks

Tunable: `swath_break_threshold` (min inliers) :contentReference[oaicite:12]{index=12}:contentReference[oaicite:13]{index=13}.

Initialize-from-plots
---------------------
.. code-block:: bash

   python main.py --config $CFG --stage initialize-from-plots   # dev partition

Requires `digitized_plot:` in YAML :contentReference[oaicite:14]{index=14}:contentReference[oaicite:15]{index=15}.

New-neighbors
-------------
.. code-block:: bash

   python main.py --config $CFG --stage new-neighbors --ids -2   # after plots
   python main.py --config $CFG --stage new-neighbors --ids top10

Finds cross-swath links inside each cluster :contentReference[oaicite:16]{index=16}:contentReference[oaicite:17]{index=17}.

Initialize-graph
----------------
.. code-block:: bash

   python main.py --config $CFG --stage initialize-graph

Prints cluster sizes; runs fine on **dev** :contentReference[oaicite:18]{index=18}:contentReference[oaicite:19]{index=19}.

Opt-links
---------
.. code-block:: bash

   python main.py --config $CFG --stage opt-links --ids top10
   # add --all-links to include every link above the threshold

Caches selection to `optim_links.p` :contentReference[oaicite:20]{index=20}:contentReference[oaicite:21]{index=21}.

Ceres-opt / Constrained-opt
---------------------------
.. code-block:: bash

   python main.py --config $CFG --stage ceres-opt       --ids top10
   python main.py --config $CFG --stage constrained-opt --ids top10

The constrained version needs `gcp_file:` in YAML :contentReference[oaicite:22]{index=22}:contentReference[oaicite:23]{index=23}.

Create-raster
-------------
.. code-block:: bash

   python main.py --config $CFG --stage create-raster \
                  --raster-type clusters --ids top10 \
                  --alpha-mode overlay --annotate graph

Generate-geotiffs / Rio merge / COG
-----------------------------------
.. code-block:: bash

   python main.py --config $CFG --stage generate-geotiffs --ids top10 --output-gsd 1
   rio merge ...                      # see PDF for loop :contentReference[oaicite:24]{index=24}:contentReference[oaicite:25]{index=25}
   rio cogeo create ...               # produce *_cog.tif :contentReference[oaicite:26]{index=26}:contentReference[oaicite:27]{index=27}

Upload & Earth Engine asset
---------------------------
.. code-block:: bash

   gcloud storage cp *.tif gs://gee_assets/mosaics/<country>/<asset_name>
   # then run notebooks/create_cog_backed_assets.ipynb  :contentReference[oaicite:28]{index=28}:contentReference[oaicite:29]{index=29}

Advanced / optional stages
--------------------------
* `stitch-across`, `refine-links` – exhaustive cross-swath search
* `estimate-gsd` – prints suggested raster resolution :contentReference[oaicite:30]{index=30}:contentReference[oaicite:31]{index=31}
* GCP collection workflow – see PDF, pages “Case 1 / Case 2” :contentReference[oaicite:32]{index=32}:contentReference[oaicite:33]{index=33}.

For full parameter docs open `config/template.yml`; every field is commented.
