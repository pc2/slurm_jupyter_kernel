try:
    from setuptools import setup;
except ImportError:
    from distutils.core import setup;

with open('README.md', 'r', encoding='utf-8') as fh:
    long_description = fh.read();

setup(
    name='slurm_jupyter_kernel',
    version='1.3',
    description='Starting a jupyter kernel using srun',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mawigh/slurm_jupyter_kernel",
    project_urls={
        "Bug Tracker": "https://github.com/mawigh/slurm_jupyter_kernel/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
    author='Marcel-Brian Wilkowsky',
    author_email='marcel.wilkowsky@hotmail.de',
    packages=['slurm_jupyter_kernel'],
    scripts=['bin/slurmkernel'],
    install_requires=['pexpect', 'pycryptodome', 'jupyter_client', 'IPython']
);
