#!/usr/bin/python3

import argparse;
import json;
import pexpect;

# handle kernel as an object
class remoteslurmkernel:

    #         add_slurm_kernel(args.displayname, args.account, args.time, args.kernel_cmd, args.partition, args.cpus, args.memory);
    def __init__ (self, connect, account, time, kernelcmd, partition="batch", cpus=None, memory=None):
        
        self.connect = json.load(open(connect));
        
        self.cpus = cpus;
        self.account = account;
        self.partition = partition;
        self.time = time;
        self.kernelcmd = kernelcmd;
        self.established = None;


        self.start_slurm_kernel();

    def start_slurm_kernel (self):

        cmd_args = [];
        default_slurm_job_name = 'jupyter_slurm_kernel';

        if not cpus == None:
            cmd_args.append(f'--cpus-per-task={cpus}');
        if not memory == None:
            cmd_args.append(f'--memory {memory}');

        cmd_args.append(f'--account={account}');
        cmd_args.append(f'--time={time}');
        cmd_args.append(f'--partition={partition}');

        cmd = f'srun {cmd_args} -J {default_slurm_kernel} -iv -u bash';
        
        if self.established == None:
            self.established = pexpect.spawn(str(cmd), timeout=500);
            
        exec_host = self.established.match.groups()[0];

        self.exec_host = exec_host;

    def kernel_state ():
        pass;


def slurm_jupyter_kernel ():


    parser = argparse.ArgumentParser('Adding jupyter kernels using slurm');

    parser.add_argument('connection_file', required=True);
    parser.add_argument('--displayname', required=True, help='Display name of the new kernel');
    parser.add_argument('--cpus', help='slurm job spec: CPUs');
    parser.add_argument('--memory', help='slurm job spec: memory allocation');
    parser.add_argument('--partition', help='slurm job spec: memory allocation');
    parser.add_argument('--account', required=True, help='slurm job spec: account name');
    parser.add_argument('--time', required=True, help='slurm job spec: running time');
    parser.add_argument('--kernel-cmd', required=True, help='command to run jupyter kernel');

    args = parser.parse_args();

    obj_kernel = remoteslurmkernel(connect=args.connection_file, account=args.account,time=args.time, kernelcmd=args.kernel_cmd, partition=args.partition, cpus=args.cpus, memory=args.memory);

    #obj.kernel_state();
