.. _installation:

************
Installation
************

This guide assumes your system already has the prerequisit dependencies.

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

Once these are setup, the installation for the acme_workflow is straightforward.

.. code-block:: bash

    conda create -n workflow -c acme -c uvcdat -c conda-forge -c lukasz processflow
    source activate workflow


Instructions on configuration and execution can be found here :ref:`Quickstart`
