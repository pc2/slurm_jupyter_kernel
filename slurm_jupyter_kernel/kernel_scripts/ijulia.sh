# input variables
# the numbers after INPUT_* will be used as variables inside the script: $1, $2, ...
INPUT_1=Load required software;module load lang JuliaHPC
INPUT_2=Julia Project Path;$HOME/ijulia
INPUT_3=Julia Depot Path;$HOME/.julia
INPUT_4=Environment variables;JULIA_NUM_THREADS=4

# commands to execute on remote host
$1
mkdir $2
cd $2
julia -e 'using Pkg; Pkg.activate("."); Pkg.add("IJulia")'
echo -e '#!/bin/bash\n$1\n"$@"' > $2/ijulia_wrapper.sh
chmod +x $2/ijulia_wrapper.sh

# kernel settings
LANGUAGE=julia
ARGV=$2/ijulia_wrapper.sh julia -i --color=yes --project=$2 $3/packages/IJulia/AQu2H/src/kernel.jl {connection_file}
ENV=$4,JULIA_DEPOT_PATH=$3