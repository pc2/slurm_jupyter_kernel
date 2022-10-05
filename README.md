# Slurm Jupyter Kernel

Create jupyter kernels and run kernels using srun

slurmkernel is able to connect to a kernel started on a compute node using SSH port forwarding.
You can specify a SSH proxy jump, if you have to jump over two hosts (e.g. a loadbalancer)

If you are an HPC user, you can also install the Python packages `notebook` and `slurm_jupyter_kernel` with the prefix `--user` into your home directory.

![How it works](imgs/how_it_works.png)

## Table of Contents

- [Slurm Jupyter Kernel](#slurm-jupyter-kernel)
  - [Table of Contents](#table-of-contents)
  - [Installation](#installation)
    - [Install using pip](#install-using-pip)
  - [Create a new kernel](#create-a-new-kernel)
    - [IPython Example](#ipython-example)
      - [Remote Host](#remote-host)
      - [Localhost](#localhost)
    - [IJulia Example](#ijulia-example)
      - [Remote Host](#remote-host-1)
      - [Localhost](#localhost-1)
    - [Set kernel-specific environment](#set-kernel-specific-environment)
  - [Using the kernel with Quarto](#using-the-kernel-with-quarto)
    - [Example](#example)
  - [Get help](#get-help)

## Installation

### Install using pip

```bash
python3 -m pip install slurm_jupyter_kernel
```

#### Install the unstable version
```bash
python3 -m pip install git+https://github.com/pc2/slurm_jupyter_kernel.git
```

## Create a new kernel

We assume to install the Jupyter kernel tools into your `$HOME` directory on your cluster.

### IPython Example

#### Remote Host

1. load required software (if necessary)
2. Create a Python virtual environment
3. Install the IPython package (ipython, ipykernel)
4. Create a wrapper script and mark it as executable

```bash
remotehost ~$ module load lang Python
remotehost ~$ python3 -m venv remotekernel/
remotehost ~$ source remotekernel/bin/activate
(remotekernel) remotehost ~$ python3 -m pip install ipython ipykernel; deactivate
remotehost ~$ echo -e '#!/bin/bash\nmodule load lang Python\n\nsource remotekernel/bin/activate\n"$@"' > remotekernel/ipy_wrapper.sh && chmod +x remotekernel/ipy_wrapper.sh
```

#### Localhost

5. Kernel Remote Slurm kernel with command `slurmkernel`

```bash
notebook ~$ slurmkernel create --displayname "Remote Python" \
--slurm-parameter="account=slurmaccount,time=00:30:00,partition=normal" \
--kernel-cmd="\$HOME/remotekernel/ipy_wrapper.sh ipython kernel -f {connection_file}" \
--proxyjump="lb.n1.pc2.uni-paderborn.de" \
--loginnode="login-0001" \
--language="python"
```

### IJulia Example

#### Remote Host

1. load required software (if necessary)
2. Set `JULIA_DEPOT_PATH`
3. Create a wrapper script and mark it as executable
4. activate environment and install IJulia

```bash
remotehost ~$ module load lang Julia
remotehost ~$ export JULIA_DEPOT_PATH=$HOME/.julia/
remotehost ~$ echo -e '#!/bin/bash\nmodule load lang Julia\n\n"$@"' > .julia/ijulia_wrapper.sh && chmod +x .julia/ijulia_wrapper.sh

remotehost ~$ julia
julia> ]
(julia) pkg> activate $HOME/.julia/
(julia) pkg> add IJulia
```

#### Localhost

5. Kernel Remote Slurm kernel with command `slurmkernel`

```bash
notebook ~$ slurmkernel create --displayname "Remote Julia" \
--slurm-parameter="account=slurmaccount,time=00:30:00,partition=normal" \
--kernel-cmd="\$HOME/.julia/ijulia_wrapper.sh julia -i --color=yes --project=\$HOME/.julia/ \$HOME/.julia/packages/IJulia/AQu2H/src/kernel.jl {connection_file}" \
--proxyjump="lb.n1.pc2.uni-paderborn.de" \
--loginnode="login-0001" \
--language="julia"
```

![Example](imgs/example.png)

### Set kernel-specific environment

If you want to set kernel specific environment variables (e.g. `JULIA_NUM_THREADS` for the number of threads) just extend the jupyter kernelspec file with `env`.

Parameter for `slurmkernel`:

`--environment="JULIA_NUM_THREADS=4"`

More information here: https://jupyter-client.readthedocs.io/en/stable/kernels.html

## Using the kernel with Quarto

What is Quarto?

https://quarto.org/

* Install kernel as shown above 
  *  Make sure that you pass the `--language` flag as well.
     *  e.g. `python` or `julia`

### Example
<img src="imgs/quarto_example.png" width="600">

## Get help

```bash
$ slurmkernel {create,list} --help

usage: Adding jupyter kernels using slurm [-h] {create,list} ...

positional arguments:
  {create,list}
    create       create a new slurm kernel
    list         list available slurm kernel

optional arguments:
  -h, --help     show this help message and exit
```
