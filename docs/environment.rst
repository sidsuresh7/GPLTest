Execution Environment
=====================

Container
---------
The entire tool-chain is bundled in

.. code-block:: bash

   /oak/stanford/groups/smhsiang/aerialhist/stitching/containers/surf_ceres.sif

Run any stage through **Singularity** to guarantee consistent libraries.

Local dev
---------
*Install once* (VS Code integrated terminal):

.. code-block:: bash

   git clone https://github.com/<org>/aerial-history-stitching.git
   cd aerial-history-stitching
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt

Sherlock modules
----------------
When you need non-Python utilities:

.. code-block:: bash

   ml avail                 # see everything
   ml python/3.9 rasterio   # load modules ad-hoc

Queues & resources
------------------
Submit heavy jobs through **Slurm**.  Typical header:

.. code-block:: bash

   #!/usr/bin/env bash
   #SBATCH -p serc,normal   # or dev for quick tests (1 CPU / ≤1 h)
   #SBATCH -c 30            # 30 CPUs match --surf_workers 6
   #SBATCH -t 24:00:00      # wall-time safety buffer

   