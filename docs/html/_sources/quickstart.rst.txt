.. quickstart:

***********
Quick Start
***********

This is a guild for a new user on a setup system. A guide for projet and environment setup
can be found here :ref::

### Anaconda

If your user doesnt have anaconda installed, you will need to install anaconda for environment and package management. You can check if you have conda by simply running ```conda``` If the command fails, your user doesnt have conda in your path. If it works, skip the anaconda installation step.

* Simply run the installer from the cached copy on the server

    ```bash /p/cscratch/acme/bin/Anaconda2-4.3.1-Linux-x86_64.sh```

* The installer will ask you some questions, unless you want to customize it in some way, just type 'yes' and hit enter for all of them.


* Start a new bash shell with the new environment variables.
    ```bash```

For a new run you'll need to create an input directory and setup your runs configuration file. Make a copy of the sample config file.
```
mkdir /p/cscratch/acme/USER_NAME/PROJECT/input
cd /p/cscratch/acme/USER_NAME/PROJECT/input
wget https://raw.githubusercontent.com/sterlingbaldwin/acme_workflow/master/run.cfg
```