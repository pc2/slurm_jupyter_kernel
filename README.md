# SLURM Jupyter Kernel

Create jupyter kernels and run kernel using srun


## Installation

### Clone Repository

```bash
git clone https://github.com/mawigh/slurm_jupyter_kernel.git
```

### Install using pip

```bash
python3 -m pip install -e slurm_jupyter_kernel/
```
## Create a new kernel

### Example

```bash
$ slurmkernel create --displayname="Python 3.8.0" --account=hpc-group --time=00:30:00 --kernel-cmd="python3 -m ipykernel_launcher -f {connection_file}"" --partiton=batch

Try to create new jupyter slurm kernel "Python 3.8.0" ...
{
  "argv": [
    "/usr/bin/python3",
    "-m",
    "slurm_jupyter_kernel",
    "--partition",
    "batch",
    "--account",
    "hpc-group",
    "--time",
    "00:30:00",
    "--kernel-cmd",
    "python3 -m ipykernel_launcher -f {connection_file}"
  ],
  "display_name": "SLURM Python 3.8.0"
}

Successfully created kernel "SLURM Python 3.8.0" :-)

```
