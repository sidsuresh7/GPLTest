Execution Environment
=====================

Choose your runtime
-------------------
You have two equivalent ways to satisfy SURF **and** keep the rest of the
dependencies stable:

#. **Python venv with legacy libraries**  
   *SURF is patented and no longer ships with wheel-based OpenCV.*  
   Create an isolated environment so its old-style packages don’t clash with
   modern ones:

   .. code-block:: bash

      python -m venv .venv && source .venv/bin/activate
      # install *exact* versions listed by the pipeline maintainers
      pip install -r requirements.txt

   The requirements pin `opencv-contrib-python==4.5.5.64`, which still
   contains SURF.

#. **Docker / Singularity container**  
   A ready-made image has OpenCV rebuilt from source with SURF enabled and
   all other libs up-to-date.  
   *If you work on Sherlock use Singularity; locally you can run the same
   image with Docker.*

   .. code-block:: bash

      singularity pull surf_ceres.sif docker://ghcr.io/<org>/surf_ceres:latest
      # example shell inside the container
      singularity exec --cleanenv surf_ceres.sif bash

   *(TO DO: when the Dockerfile is published, drop it in `docs/environment/`
   and reference it here.)*

Sherlock modules
----------------
When you need extra command-line tools (e.g. `gcloud`, `rio`):

.. code-block:: bash

   ml avail                         # discover modules
   ml python/3.9 rasterio           # load just-in-time

Queues & resources
------------------
Typical Slurm header for compute-heavy stages:

.. code-block:: bash

   #!/usr/bin/env bash
   #SBATCH -p serc,normal        # or dev for quick, small jobs
   #SBATCH -c 30                 # CPUs = surf_workers * 5 is a good rule
   #SBATCH -t 24:00:00           # generous wall-time buffer


