.. acme_workflow documentation master file, created by
   sphinx-quickstart on Tue Aug 15 16:44:35 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

*****************************
acme_workflow's documentation
*****************************

What is the automated workflow?
===============================

The automated workflow is a command line tool to automatically run post processing jobs for ACME model output.

The tool takes a single configuration files and runs a series of long running transfer
and processing jobs on any amount of model output, running the set of jobs on any number of set lengths. The output
doesn't have to exist before the tool is run, meaning it can be started at the same time as the model and as data is
generated will transfer it, and start the processing and diagnostics as soon as the first complete set is available.

Transfer jobs will be generated to match the data requirements of the processing jobs, and the processing jobs will 
wait to run until after the data has been made available. Once the diagnostics complete, the tool manages hosting the 
images and emails links with the completed output to the user. 

**Jobs:**

* Globus Transfer
* AMWG diagnostic
* Regridding and Climatologies
* Time series variable extraction
* A-Prime diagnostic
* ACME diags (in development)

Each processing job has an optional number of other jobs it should wait on, for example
AMWG will wait for the regridded climatologies to be generated before starting its
run.

**Dependencies:**

* Anaconda_
* Slurm_
* Globus_
* NCL_
* APACHE_

.. _Anaconda: https://www.continuum.io/downloads
.. _Slurm: https://slurm.schedmd.com/
.. _Globus: https://www.globus.org/
.. _NCL: https://www.ncl.ucar.edu/
.. _APACHE: https://www.digitalocean.com/community/tutorials/how-to-configure-the-apache-web-server-on-an-ubuntu-or-debian-vps


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation
   quickstart
   transfer
   amwg
   ncclimo
   aprime
   acme_diags
   sample_config

