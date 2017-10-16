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

    conda create -n workflow -c acme -c conda-forge -c uvcdat  -c lukasz processflow
    source activate workflow

Alternately you may want to use the nightly build. This is the more experimental branch where new changes are pushed before being merged into the main build

.. code-block:: bash

    conda create -n workflow -c acme/label/nightly -c conda-forge -c uvcdat  -c lukasz processflow
    source activate workflow

If you alreayd have an installation and want to upgrade, make sure you're in your environment and then run:

.. code-block:: bash

    conda install -c acme -c conda-forge -c uvcdat  -c lukasz processflow

Or upgrade from the nightly:

.. code-block:: bash

    conda install -c acme/label/nightly -c conda-forge -c uvcdat  -c lukasz processflow

Instructions on configuration and execution can be found here :ref:`Quickstart`
