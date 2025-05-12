Deep‑Dive: Pipeline Stages
==========================

This chapter is the **encyclopaedia** version: exhaustive descriptions,
internal data schemas, algorithmic references, and parameter sensitivity
analyses for every stage.  Skim during debug sessions; print sections when
on‑boarding new lab members.

Legend
------
* **img_df** – GeoPandas dataframe keyed by *(idx0, idx1)* (film, frame).
* **links_df** – Pandas dataframe keyed by *(idx0_a, idx1_a, idx0_b, idx1_b)*.
* **cluster_id** semantics:

  * −2 – images placed via prior (sortie plot or GCP)
  * −1 – uninitialised
  * ≥0 – numbered clusters

Initialize
----------
**I/O.**  Scans directory tree, infers film & frame from filename regex
`r"NCAP_(?P<film>\d+)_(?P<frame>\d+)"`.  Adds columns:

====================  =================================================
Column                Meaning
====================  =================================================
`film`                Original film roll id
`frame`               Sequential id inside roll
`image_path`          Absolute path on OAK
`width`,`height`      Raw scanner resolution
`geometry`            *None* (filled later)
`cluster_id`          −1
====================  =================================================

Failure modes
~~~~~~~~~~~~~
* **Missing frame numbers** – some contracts use alphabetic suffixes (e.g. 10A).
  Provide `filename_regex` in YAML to override.
* **Duplicate (film,frame)** – cleaned by keeping the newest modified‑time.

Crop
----
Two‑tier mask:

1. **Adaptive background** – flood‑fill the smooth region outside photo.
2. **Contract‑specific frame** – rectangle or rounded corners trimmed by
   `margin_*`.

Mathematical formulation
~~~~~~~~~~~~~~~~~~~~~~~~
Adaptive mask uses variance of Gaussian‑blurred greyscale:

.. math::
   M(i,j) = \begin{cases}
              1 & \text{if } \sigma_{\text{local}}(i,j) > T_\text{std}
              0 & \text{otherwise}
            \end{cases}

Bounding rectangle extracted by argmin/argmax; stored in `img_df` so later
stages can crop *on‑the‑fly* without rewriting millions of JPEGs.

Inspect‑cropping prints an HTML gallery (Jinja template in `src/vis/`).

Featurize
---------
**Algorithm.** SURF 128‑D descriptor (we truncate to 64‑D to halve disk and
speed up FLANN).  Keypoints pruned at two places:

* Detector: `hessian_threshold` (SURF paper §4.1).
* Dataset‑wide max: keep top‑K by response to cap RAM.

Compressed as blosc‑zstd inside HDF5 → 200 keypoints ≈ 24 kB.

Swath‑breaks
------------
*Candidate links.*  For every `(img_i, img_{i+1})` in folder order:

#. Load keypoints & descriptors.
#. Match via FLANN Index (KD‑tree, 12 trees).
#. Apply Lowe ratio test (≤ 0.8).
#. Fit affine with RANSAC (1000 iters, reprojection ≈ 5 px).
#. Count inliers.

If `inliers ≥ swath_break_threshold` ⇒ link accepted.

Complexity: **O(N)** links for **N** frames vs **O(N²)** naïve.

Initialize‑graph
----------------
Builds clusters as *union‑find* on swath nodes.  Link weight = ∑inliers over
all image‑pairs between two swaths, pruned by
`individual_link_threshold` → `cluster_inlier_threshold`.

Graph Rectification (optional)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Long‑swath drift corrected by linear regression of centroid positions, fixing
scale and yaw so optimisation starts close to manifold optimum (prevents Ceres
from falling into local minima).

Opt‑links
---------
Purpose: keep optimisation tractable by capping degree of each node.
Selection rules:

* **Within‑swath**: keep strongest `n_within` links from each image.
* **Across‑swath**: keep strongest `n_across` links.
* **Swath‑level**: stop once a swath connects to `n_swath_neighbors` others.
* Absolute inlier floor: `optim_inclusion_threshold`.

Outputs cached to `optim_links_<hash>.p` so repeated runs skip recomputation.

Ceres‑opt & Global‑opt
---------------------
Both solve a bundle adjustment problem in SE(2)×ℝ (x, y, θ, s):

.. math::
   \min_{\{T_i\}} \sum_{(i,j)∈E} \| T_j^{-1} T_i − \hat{T}_{ij} \|_Σ²

where `T_i` are optimisable transforms, `\hat{T}` are measured links, and Σ is
scaled by 1/inliers.

* **Ceres** uses sparse Levenberg‑Marquardt (CPU, no GPU needed).
* **Global‑opt** uses PyTorch Adam, optionally GPU.

Create‑raster
-------------
For each cluster:

#. Compute canvas bounds by transforming image footprints.
#. Allocate mem‑mapped RGB array (huge TIFF manageable via `rasterio.Env(GTiff)`
   blocksize).
#. For overlay mode draw images in arbitrary order; for blend mode accumulate
   alpha‑weighted arrays then divide.
#. Save GeoTIFF with proper GeoTransform.

Tip: use `estimate-gsd` beforehand to cap file size; 1 m/px is usually enough
for 1940s aerial film.

Advanced stages
---------------
* **manual-stitch** – brute‑force all pairs across two swaths; use when flight
  log is unreliable.
* **stitch-across / refine-links** – sub‑sampled keypoint search; days on large
  contracts, but finds the last 1% of links.
* **initialize-from-gcps / constrained-opt** – integrate ground control points
  for absolute georeference; requires `gcps.csv` with WGS84 coordinates.

Data lineage map
----------------
.. mermaid::

   graph TD
     A(raw images) -->|initialize| B(img_df)
     B -->|crop| C{img_df+bounds}
     C -->|featurize| D(SURF cache)
     C -->|swath-breaks| E(links_df 1)
     D --> E
     E -->|initialize-graph| F(graph)
     F -->|new-neighbors| G(links_df 2)
     G -->|opt-links| H(curated links)
     H -->|ceres-opt| I(optim img_df)
     I -->|create-raster| J(GeoTIFF/COG)
