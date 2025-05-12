Quick-start Workflow
====================

1. **Clone & configure**

   .. code-block:: bash

      git clone https://github.com/<org>/aerial-history-stitching.git
      cd aerial-history-stitching
      cp configs/template.yml configs/gambia_53.yml   # edit paths & margins

2. **Run the pipeline**

   .. code-block:: bash

      singularity run containers/surf_ceres.sif \
          python main.py --config configs/gambia_53.yml --stage initialize
      # …then crop, featurize, swath-breaks, etc.

If something fails, jump to :doc:`stages` for a stage-by-stage checklist.

Git hygiene
-----------
* `git pull` **before** you start – the cluster and your laptop must match.  
* Use feature branches for experiment scripts and merge via PRs to keep the
  history linear.  
* Recover from mistakes with `git reset --hard <COMMIT>` (works only if changes
  are committed or stashed).  

