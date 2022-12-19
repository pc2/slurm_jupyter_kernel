# input variables
# the numbers after INPUT_* will be used as variables inside the script: $1, $2, ...
INPUT_1=Load required software;module load lang Python
INPUT_2=Location to install;$HOME

# commands to execute on remote host
$1
python3 -m venv $2/ipython_venv
source $2/ipython_venv/bin/activate
python3 -m pip install ipython ipykernel
deactivate
echo -e '#!/bin/bash\n$1\nsource $2/ipython_venv/bin/activate\n"$@"' > $2/ipython_venv/ipy_wrapper.sh
chmod +x $2/ipython_venv/ipy_wrapper.sh

# kernel settings
LANGUAGE=python
ARGV=$2/ipython_venv/ipy_wrapper.sh ipython kernel -f {connection_file}