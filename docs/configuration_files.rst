Configuration Files
===================

Every run of the pipeline is driven by a **YAML** config.  
Keep a separate file per contract or country so you can tweak paths
without touching code.

Minimal skeleton
----------------
.. code-block:: yaml

   # ─── I/O paths ───────────────────────────────────────────────────────────────
   raw_images_folder:   /oak/…/datasets/raw/<COUNTRY>/<CONTRACT>
   img_cache_folder:    /scratch/…/cache/<COUNTRY>/<CONTRACT>/SURF
   raster_output_folder:/oak/…/results/<COUNTRY>/<CONTRACT>

   # ─── Runtime knobs ───────────────────────────────────────────────────────────
   surf_workers: 6            # surf_workers * 5 ≈ requested CPUs
   margin_top:    40          # px crop margins
   margin_bottom: 40
   …

Key fields
----------
* **raw_images_folder** – where `.jpg` scans live.  
* **img_cache_folder**  – SURF key-point HDF5s are cached here.  
* **raster_output_folder** – anything georeferenced lands here.  
* **digitized_plot** – optional sortie-plot CSV; enables *initialize-from-plots*.

Tips
----
* Treat the YAML as “code” – commit it to Git so every run is reproducible.  
* Keep your paths on **OAK** for persistence; put temp artefacts on **SCRATCH**.  
* When you change only cropping margins you *don’t* have to re-featurize; rerun
  the **crop** stage and then continue.  
