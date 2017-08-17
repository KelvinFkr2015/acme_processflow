.. _quickstart:

***********
Quick Start
***********

This is a guide for a new user on a system thats already been properly setup. For new users starting from scratch please referece to the
:ref:`Installation` guide. 


Anaconda
--------

You will need to either use an existing conda environment or create your own. On acme1 and aims4 prebuilt envs can be found 
at /p/cscratch/acme/bin/acme. Otherwise you can create your own environment by navigating to the top of the acme_workflow repo
and running the command:

.. code-block: bash

    conda env create -f env.yml
    source activate workflow


Run Configuration
-----------------

The acme_workflow config file contains all settings required to setup a run. Although the config file has many options, most of them
are only useful in non-default environments or to advanced users. For a basic run, the only keys that need to be changed are:


**output_path**
The path to where all the output should be stored.

**data_cache_path**
The path to where model data should be cached.

**source_path**
This is the path on the remote machine to look for data.


**simulation_start_year**
The start year of the simulation.

**simulation_end_year**
The expected end year. This can be set to year 100 when the simulation is just starting, and the acme_workflow will continuously poll for new data

**exeriment**
The name of the experiment.

**set_frequency**
The acme_workflow breaks the simulation into groups based on how much data you want the jobs to run on. For example if you wanted AMWG to run on every 10 years, but also on every 50 years, you could have set_frequency = 10, 50, and for every group of 10 years and 50 years you would get the jobs for that length run. In this example, with 50 years of output, you would get sets from 1-10, 11-20, 21-30, 31-40, 41-50, 1-50

**set_jobs**
Which jobs to run on which sets. This allows you to have different subsets of jobs run on different set lengths. If you dont want a job to run at all, keep the key for the job (the code is expecting it), but leave the value empty.

You can find a :ref:`Sample` Configuration here.


Execution
---------

The acme_workflow has two run modes, interactive and headless. In headless mode the current run status is written out to a file named run_state.txt under the output directory.


.. code-block:: bash

    usage: workflow.py [-h] [-c CONFIG] [-v] [-d] [-n] [-r] [-l LOG] [-u] [-m]
                    [-V] [-s SIZE]

    optional arguments:
    -h, --help            show this help message and exit
    -c CONFIG, --config CONFIG
                            Path to configuration file.
    -n, --no-ui           Turn off the GUI.
    -l LOG, --log LOG     Path to logging output file.
    -u, --no-cleanup      Dont perform pre or post run cleanup. This will leave
                            all run scripts in place.
    -m, --no-monitor      Dont run the remote monitor or move any files over
                            globus.
    -s SIZE, --size SIZE  The maximume size in gigabytes of a single transfer,
                            defaults to 100. Must be larger then the largest
                            single file.

When run in interactive mode, the acme_workflow will exit if the terminal window is closed. For long running jobs, the best run method is to make sure the source and destination globus nodes have been activated with your credentials, and then run

.. code-block:: bash

    nohup python workflow.py -c /PATH/TO/YOUR/CONFIG --no-ui &

Once the run starts, you will be prompted to authenticate with globus. Simply copy the address and paste into your browser. You will be presented with a page to choose which OAuth provided to use, its recommended that you use the default globus ID provider.

.. image:: https://github.com/sterlingbaldwin/acme_workflow/blob/master/doc/images/Globus_login_example.png?raw=true

Once you have entered your credentials and logged in, you will be given a randomly generated key, copy that key and paste it into the terminal prompt

.. image:: https://github.com/sterlingbaldwin/acme_workflow/blob/master/doc/images/Globus_login_token_example.png?raw=true
.. image:: https://github.com/sterlingbaldwin/acme_workflow/blob/master/doc/images/Globus_login_token_complete.png?raw=true

Once you have logged into globus, each data node will need to be activated with your account. This activation can last for days, but periodically needs to be re run. If the node needs to be activated you will be prompted, if your credentials are still cached on the node this step will be skipped.

.. image:: https://github.com/sterlingbaldwin/acme_workflow/blob/master/doc/images/Globus_activate_endpoint_example.png?raw=true

.. image:: https://github.com/sterlingbaldwin/acme_workflow/blob/master/doc/images/Globus_activate_endpoint_web.png?raw=true



Once a run starts in interactive mode, you should see the job sets listed, and the jobs should populate.

.. image:: https://github.com/sterlingbaldwin/acme_workflow/blob/master/doc/images/initial_run.png?raw=true
