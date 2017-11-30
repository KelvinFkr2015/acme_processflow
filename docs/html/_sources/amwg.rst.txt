***************
AMWG Diagnostic
***************

The `AMWG Diagsnostic <http://www.cesm.ucar.edu/working_groups/Atmosphere/amwg-diagnostics-package/>`_ is the standard diagnostic package.

Configuration
-------------

.. code-block:: python

    [global]
    ...
    set_frequency = SOME_LENGTH

    [[set_jobs]]
        ncclimo = SOME_LENGTH
        amwg = SOME_LENGTH

    [amwg]
    # The location of the amwg code
    diag_home = /p/cscratch/acme/amwg/amwg_diag

    # The directory to copy output to for hosting
    host_directory = amwg

Dependencies
------------

For each year set that AMWG is configured to run, it requires regridded climatologies created by ncclimo. This means that you have to make sure
that for each year_set ncclimo is also set to run. AMWG will wait for ncclimo to finish generating climatologies before starting its run.
