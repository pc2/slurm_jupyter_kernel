try:
    from setuptools import setup;
except ImportError:
    from distutils.core import setup;

with open('README.md', 'r', encoding='utf-8') as fh:
    long_description = fh.read();

setup(
    name='slurm_jupyter_kernel',
    version='1.8',
    description='Manage and start jupyter slurm kernels',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pc2/slurm_jupyter_kernel",
    project_urls={
        "Bug Tracker": "https://github.com/pc2/slurm_jupyter_kernel/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
    author='Marcel-Brian Wilkowsky',
    author_email='marcel.wilkowsky@uni-paderborn.de',
    packages=['slurm_jupyter_kernel'],
    scripts=['bin/slurmkernel'],
    install_requires=['pexpect', 'jupyter_client', 'IPython']
);
