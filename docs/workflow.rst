Stitching Pipeline Procedure and Workflow
============================

DataSet Spreadsheet
-------------------
Row: survey that the British government decided they want to take over a piece of land  
Sorted Plots – maps that have the trajectory of the plane on the maps  

1. Create and Configure Your `.yml` File
----------------------------------------
- **What stays constant** (don’t touch):  
  the structure and keys in `gambia_124.yml` (or any existing config).
- **What you need to edit** (values you must change):
  
  1. Copy it to a new file for your survey:
  
     .. code-block:: bash

        cp gambia_124.yml gambia_53.yml

  2. Update all folder paths under these keys:

     .. code-block:: yaml

        img_cache_folder:        /scratch/groups/smhsiang/ahp/stitching/cache/Gambia/gambia_53/SURF
        checkpoint_cache_folder: /oak/stanford/groups/smhsiang/aerialhist/stitching/results/Gambia/gambia_53
        raster_output_folder:    /oak/stanford/groups/smhsiang/aerialhist/stitching/results/Gambia/gambia_53

  3. *(Optional)* Add digitized-plot data:

     .. code-block:: yaml

        digitized_plot: /oak/stanford/groups/smhsiang/aerialhist/datasets/scan_lines/Gambia/Gambia_scan_lines.csv


2. Initialize Stage
-------------------
- **What stays constant**:
  - Singularity image:  
    `/oak/stanford/groups/smhsiang/aerialhist/stitching/containers/surf_ceres.sif`
  - Python entry-point:  
    `/home/users/sidsur/aerial-history-stitching/main.py`

- **What to edit**:
  - `--config` path: point to your new YAML:
    
    .. code-block:: bash

       --config /oak/stanford/groups/smhsiang/aerialhist/stitching/config/Gambia/gambia_53.yml

  - `--stage` flag:

    .. code-block:: bash

       --stage initialize

- **Sample command**:

  .. code-block:: bash

     singularity run /oak/stanford/groups/smhsiang/aerialhist/stitching/containers/surf_ceres.sif \
         python3 /home/users/sidsur/aerial-history-stitching/main.py \
         --config /oak/stanford/groups/smhsiang/aerialhist/stitching/config/Gambia/gambia_53.yml \
         --stage initialize


3. Cropping & Inspection
-------------------------
1. **Edit your `.yml`**  
   - Constant keys: `margin_bottom`, `margin_left`, `margin_top`, `margin_right`  
   - Edit values to tweak cropping margins.

2. **Prepare your SLURM script**  
   - Constant: Singularity image and Python entry-point (same as Initialize).  
   - Edit:
     - `#SBATCH -c 30`  (allocate 30 CPUs)
     - `--stage crop` → later change to `--stage inspect-crop`
     - `--config` path (your config file)

3. **Workflow**  
   - Submit crop job:

     .. code-block:: bash

        sbatch crop_gambia_53.slurm

   - In Jupyter, open the “Inspect Crop” notebook in the `raster_output_folder` to view sample masks.  
   - Adjust margins in `.yml` and rerun with `--stage inspect-crop`.


4. Featurization
----------------
- **Purpose**: detect and describe keypoints using SURF.
- **What stays constant**:
  - The SURF algorithm
  - Outputs `.hdf5` files to `img_cache_folder`

- **What to edit in SLURM**:
  - `--stage featurize`
  - `--config` path
  - CPU count (`#SBATCH -c 30`)

- **Run**:

  .. code-block:: bash

     sbatch featurize_gambia_53.slurm


5. Swath Breaks
---------------
- **Purpose**: link consecutive images by matching inliers.
- **Config edits**:
  - Constant key: `inlier_threshold` (already set)
  - Edit only to change link strictness.
- **SLURM changes**:
  - `--stage swath-break`
  - `#SBATCH -c 30`
  - `--config` (unchanged path)
- **Run**:

  .. code-block:: bash

     sbatch swathbreak_gambia_53.slurm


6. Sortie Plots (Optional)
--------------------------
- **When you have DOS_PLOTS**:
  1. Edit your `.yml` to add:

     .. code-block:: yaml

        digitized_plot: /oak/stanford/groups/smhsiang/aerialhist/datasets/scan_lines/Gambia/Gambia_scan_lines.csv

  2. In SLURM script:
     - Change `--stage` to `initialize-from-plots`
     - Switch partition: `#SBATCH -p dev`
     - Remove CPU line (uses 1 CPU)

  3. **Run**:

     .. code-block:: bash

        sbatch plots_gambia_53.slurm


7. New Neighbors
----------------
- **Purpose**: find links within clusters only.
- **SLURM edits**:
  - `--stage new-neighbors`
  - `--ids -2`
  - `#SBATCH -p serc,normal`
  - `#SBATCH -c 30`
- **Run**:

  .. code-block:: bash

     sbatch newneighbors_gambia_53.slurm


Tips for All SLURM Scripts
--------------------------
- **Keep constant**: lines loading modules or the Singularity container.  
- **Always edit**:
  - `--config` path  
  - `--stage` name  
  - Any stage‑specific flags (e.g. `--ids`)  
  - CPU or partition directives under `#SBATCH`