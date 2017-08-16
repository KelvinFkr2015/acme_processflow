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

    git clone git@github.com:ACME-Climate/acme_workflow.git
    cd acme_workflow
    conda env create -f env.yml
    source activate workflow

Instructions on configuration and execution can be found here :ref:`Quickstart`
