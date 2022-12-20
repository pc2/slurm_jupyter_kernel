# input variables
# the numbers after INPUT_* will be used as variables inside the script: $1, $2, ...
INPUT_1=Command to load required software;module load lang Python
INPUT_2=Path to Python virtual env;$HOME/ipython_venv

# commands to execute on remote host
$1
python3 -m venv $2
source $2/bin/activate
python3 -m pip install ipython ipykernel
deactivate
echo -e '#!/bin/bash\n$1\nsource $2/bin/activate\n"$@"' > $2/ipy_wrapper.sh
chmod +x $2/ipy_wrapper.sh

# kernel settings
LANGUAGE=python
ARGV=$2/ipy_wrapper.sh ipython kernel -f {connection_file}