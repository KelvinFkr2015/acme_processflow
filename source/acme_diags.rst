***************
ACME Diagnostic
***************

The `ACMEDiags <https://github.com/ACME-Climate/acme_diags>`_ is the Diagnostic
ploting software made at LLNL to modernize many of the features of AMWG.

Configuration
-------------

.. code-block:: python

    [global]
    ...
    set_frequency = SOME_LENGTH

        [[patterns]]
        ATM = "cam.h0"
        ...
    
        [[set_jobs]]
        ncclimo = SOME_LENGTH
        acme_diags = SOME_LENGTH
    
    [acme_diags]
    # The directory to copy output to for web hosting
    # This path is relative to the global host_prefix
    host_directory = acme-diags

    # The base of the url to serve through apache
    # This is the prefix for the url generation, the path to access the output from apache
    * for example this would construct the following url https://your_server.gov/acme-diags/your_data_set
    host_url_prefix = acme-diags

    # ACME diags can use several backends to generate plots, currently matplotlib and vcs are supported.
    backend = vcs

    # the color map to use
    diff_colormap = bl_to_darkred

    # seasons list to generate plots for 
    seasons = DJF, MAM, JJA, SON, ANN

    # path to observation data
    reference_data_path = /p/cscratch/acme/data/obs_data_20140804

    # list of diagnostic sets to run
    sets = 4, 5

Dependencies
------------

The ACME diagnostic is very similar to AMWG but more modern. It has the same data requirement that ncclimo produce regridded climatologies.

