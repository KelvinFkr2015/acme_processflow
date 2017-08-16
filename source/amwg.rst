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
    # The location of the amwg code. 
    # This is the install directory for the AMWG code
    diag_home = /p/cscratch/acme/amwg/amwg_diag

    # The directory to copy output to for web hosting
    # This path is relative to the global host_prefix
    host_directory = /amwg/

    # The base of the url to serve through apache
    # This is the prefix for the url generation, the path to access the output from apache
    * for example this would construct the following url https://your_server.gov/amwg/your_data_set
    host_url_prefix = amwg

Dependencies
------------

For each year set that AMWG is configured to run, it requires regridded climatologies created by ncclimo. This means that you have to make sure
that for its year set ncclimo is also set to run. AMWG will wait for ncclimo to finish generating climatologies before starting its run.
