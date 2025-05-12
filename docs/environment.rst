--------------------------------------------------------------------
environment.rst
--------------------------------------------------------------------
```rst
Execution Environment
=====================

Why two environments?
---------------------
**SURF**—the keypoint detector this pipeline relies on—is
*patent‑encumbered*.  Newer versions of `opencv‑python` do not ship SURF to
avoid licensing headaches.  You therefore face a trade‑off:

* Keep using *legacy* OpenCV 4.5.x wheels (easy, but older deps).
* Build or pull a *container* with SURF compiled into OpenCV 4.9+ (modern libs,
  reproducible, slightly steeper learning curve).

The pipeline works in either scenario; pick one and stick to it to prevent
mix‑and‑match chaos.

──────────────
Option 1 – venv
──────────────
Suitable when you **don’t** need the absolute latest NumPy/PyTorch and you’re
OK with a Python‑only workflow (no GPU acceleration required).

.. code-block:: bash

   # create & activate
   python -m venv .venv && source .venv/bin/activate

   # freeze OpenCV at 4.5.5.64 – last wheel that bundles SURF
   echo "opencv-contrib-python==4.5.5.64" >> requirements.txt
   pip install -r requirements.txt

   # verify
   python - <<'PY'
   import cv2, sys
   has_surf = hasattr(cv2, 'xfeatures2d') and hasattr(cv2.xfeatures2d, 'SURF_create')
   sys.exit(0 if has_surf else 1)
   PY

`cv2.error: The called functionality is disabled` ⇒ your wheel is too new.

───────────────
Option 2 – container
───────────────
Recommended for **Sherlock** and for contributors who value reproducibility.
The project maintains a GitHub Container Registry image built like so:

.. code-block:: docker
   :caption: (excerpt) Dockerfile

   FROM nvidia/cuda:12.4.1-runtime-ubuntu22.04
   ARG OPENCV_VERSION=4.9.0
   RUN apt-get update && apt-get install -y build-essential cmake git \
       libjpeg-dev libpng-dev libtiff-dev libgl1-mesa-dev && rm -rf /var/lib/apt/lists/*
   RUN git clone --branch ${OPENCV_VERSION} https://github.com/opencv/opencv.git && \
       git clone --branch ${OPENCV_VERSION} https://github.com/opencv/opencv_contrib.git && \
       mkdir build && cd build && \
       cmake ../opencv -DOPENCV_EXTRA_MODULES_PATH=../opencv_contrib/modules \
             -DBUILD_opencv_xfeatures2d=ON -DWITH_CUDA=ON \
             -DBUILD_LIST=features2d,highgui,imgcodecs,videoio,calib3d && \
       make -j$(nproc) && make install && ldconfig && cd .. && rm -rf build opencv*

   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt

Pull and use via Singularity (no root required on HPC):

.. code-block:: bash

   singularity pull surf_ceres.sif docker://ghcr.io/gpl/surf_ceres:latest
   singularity shell --cleanenv surf_ceres.sif   # drops you in /workspace

GPU acceleration inside Singularity works automatically on Sherlock because
`--nv` is injected by the wrapper script.

Local Tips
~~~~~~~~~~
* On macOS w/ Apple Silicon the wheel route is simpler (Docker lacks native
  SURF builds for ARM).  Stick to the venv.
* Use **VS Code Remote – Containers** to develop inside the image on a laptop.

Sherlock Cheat‑Sheet
--------------------
========================  ==============================================
Action                      Command
========================  ==============================================
Show quotas (SCRATCH/OAK)  ``lquota``
Available modules          ``ml avail``
Launch JupyterLab          ``sherlock_on_demand --partition dev``
See running jobs           ``squeue -u $USER``
Cancel job 123456          ``scancel 123456``
Inspect resources used     ``sacct -j 123456 --format=JobID%15,MaxRSS,Elapsed``
========================  ==============================================

Best‑practice Slurm header
--------------------------
.. code-block:: bash

   #!/usr/bin/env bash
   #SBATCH -J gambia_53-featurize        # job name shows stage & contract
   #SBATCH -o logs/%x.%j.out             # stdout
   #SBATCH -e logs/%x.%j.err             # stderr
   #SBATCH -p serc,normal                # dev if <1h & 1 CPU
   #SBATCH -c 30                         # CPUs ← surf_workers*5
   #SBATCH -t 48:00:00                   # generous walltime
   #SBATCH --mail-type=FAIL              # email on crash

   module purge && module load singularity/4.0.2
   singularity exec --cleanenv surf_ceres.sif \
       python main.py --config configs/gambia_53.yml --stage featurize
