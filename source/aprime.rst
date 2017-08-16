******************
A-Prime Diagnostic
******************

`A-Prime <https://github.com/ACME-Climate/a-prime>`_ runs a subset of atmospheric plots, as well
as the MPAS ocean analysis. It is also known as the Coupled Diagnostics.

Configuration
-------------

The A-Prime diagnostics required significantly more data then other diagnostic packages. It can be run in atmospheric only mode by turning off the 
run_ocean flag, in which case it only requires the ATM files and the RPT files. With run_ocean turned on, it requires all the following data.

.. code-block:: python

    [global]
    ...
    set_frequency = SOME_LENGTH

        [[patterns]]
        ATM = "cam.h0"
        MPAS_AM = "mpaso.hist.am.timeSeriesStatsMonthly"
        MPAS_CICE = "mpascice.hist.am.timeSeriesStatsMonthly"
        MPAS_RST = "mpaso.rst.0"
        MPAS_O_IN = "mpas-o_in"
        MPAS_CICE_IN = "mpas-cice_in"
        RPT = "rpointer"
        ...
    
        [[set_jobs]]
        coupled_diags = SOME_LENGTH

Dependencies
------------

For the MPAS analysis to run, A-Prime needs atmospheric as well as all the MPAS ocean files. Because it computes its own climatologies it does
not require ncclimo to run first.
