# Slurm Jupyter Kernel

Create jupyter kernels and run kernels using srun

slurmkernel is able to connect to a kernel started on a compute node using SSH port forwarding.
You can specify a SSH proxy jump, if you have to jump over two hosts (e.g. a loadbalancer)

If you are an HPC user, you can also install the Python packages `notebook` and `slurm_jupyter_kernel` with the prefix `--user` into your home directory.

To allow users to access the compute node without a password, the following PAM module should have been configured:
https://slurm.schedmd.com/pam_slurm_adopt.html

![How it works](imgs/how_it_works.png)

## Installation

### Install using pip

```bash
python3 -m pip install git+https://github.com/pc2/slurm_jupyter_kernel.git@remote_execution
```

## Create a new kernel

### Python


#### On the remote host

```bash
noctua1 me/ $ export MYRKERNEL_DIR=/scratch/me/rkernel/py/
 
noctua1 me/ $ cd $MYRKERNEL_DIR
noctua1 py $ module load lang Python # load python environment
noctua1 py $ python -m venv ipython_venv # create a venv for the IPython kernel
noctua1 py $ source ipython_venv/bin/activate # activate environment
 
(ipython_venv) noctua1 py $ python3 -m pip install --upgrade pip
(ipython_venv) noctua1 py $ python3 -m pip install ipython ipykernel
(ipython_venv) noctua1 py $ echo -e '#!/bin/bash\nmodule load lang Python\n"$@"' > ipy_wrapper.sh
(ipython_venv) noctua1 py $ chmod +x ipy_wrapper.sh
```

#### Localhost

```bash
notebook $ export MYRKERNEL_DIR=/scratch/me/rkernel/py/

notebook $ slurmkernel create --displayname "Noctua 1 Python" \
--slurm-parameter="account=slurmaccount,time=00:30:00,partition=normal" \
--kernel-cmd="$MYRKERNEL_DIR/ipy_wrapper.sh ipython kernel -f {connection_file}" \
--proxyjump="lb.n1.pc2.uni-paderborn.de" \
--loginnode="login-0001"
```

![Example](imgs/example.png)

### Get help

```bash
$ slurmkernel --help

usage: Adding jupyter kernels using slurm [-h] {create} ...

positional arguments:
  {create}
    create    create a new slurm kernel

optional arguments:
  -h, --help  show this help message and exit

```


