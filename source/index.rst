.. acme_workflow documentation master file, created by
   sphinx-quickstart on Tue Aug 15 16:44:35 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

*****************************
acme_workflow's documentation
*****************************

What is the automated workflow?
===============================

The automated workflow is a command line tool to manage post processing for ACME model output

The acme_workflow takes a single configuration files and runs a series of long running transfer
and processing jobs. There are two main types of jobs, processing and transfer. Transfer jobs
will be generated to match the data requirements of the processing jobs, and the processing jobs
will wait to run until after the data has been made available. 

** Job Types: **
* Globus Transfer
* AMWG diagnostic
* Regridding and Climatologies
* Time series variable extraction
* A-Prime diagnostic
* ACME diags (planned)

Each processing job has an optional of other jobs it should wait on, for example
AMWG will wait for the regridded climatologies to be generated before starting its
run.

** Dependencies: **
* `Anaconda <https://www.continuum.io/downloads>`_
* `Slurm <https://slurm.schedmd.com/>`_
* `Globus <https://www.globus.org/>`_
* `NCL <https://www.ncl.ucar.edu/>`_



.. toctree::
   :maxdepth: 2
   :caption: Contents:

   quickstart
   transfer
   amwg
   ncclimo
   aprime
   acme_diags

