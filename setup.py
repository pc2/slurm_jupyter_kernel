try:
    from setuptools import setup;
except ImportError:
    from distutils.core import setup;

setup(
    name='slurm_jupyter_kernel',
    version='0.1',
    description='Starting a jupyter kernel using srun',
    author='Marcel-Brian Wilkowsky',
    author_email='marcel.wilkowsky@hotmail.de',
    packages=['slurm_jupyter_kernel'],
    scripts=['bin/slurmkernel'],
    install_requires=['pexpect']
);
