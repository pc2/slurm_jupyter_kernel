#!/usr/bin/python3

import argparse;
import json;
import pexpect;
import logging;

logging.basicConfig(level=logging.DEBUG);

# handle kernel as an object
class remoteslurmkernel:

    def __init__ (self, account, time, kernelcmd, connection_file, partition="batch", cpus=None, memory=None, reservation=None):
        
        self.cpus = cpus;
        self.account = account;
        self.partition = partition;
        self.time = time;
        self.memory = memory;
        self.reservation = reservation;
        self.kernelcmd = kernelcmd;
        self.slurm_session = None;
        self.connection_file = json.load(connection_file);

        self.start_slurm_kernel();

    def start_slurm_kernel (self):

        cmd_args = [];
        default_slurm_job_name = 'jupyter_slurm_kernel';

        if not self.cpus == None:
            cmd_args.append(f'--cpus-per-task={self.cpus}');
        if not self.memory == None:
            cmd_args.append(f'--memory={self.memory}');
        if not self.reservation == None:
            cmd_args.append(f'--reservation={self.reservation}');

        cmd_args.append(f'--account={self.account}');
        cmd_args.append(f'--time={self.time}');
        cmd_args.append(f'--partition={self.partition}');

        cmd_args = " ".join(cmd_args);
        cmd = f'srun {cmd_args} -J {default_slurm_job_name} -vu bash -i';

        logging.debug(f"Running slurm kernel command: {cmd}");
        
        self.slurm_session = pexpect.spawn(str(cmd), timeout=500);
       
        if not self.slurm_session == None:
            kernel_conn = json.dumps(self.connection_file);
            self.slurm_session.sendline(kernel_conn);

            logging.debug(f"Try to initialize kernel with command: {self.kernelcmd}");

            kernel_start = self.kernelcmd;
            self.slurm_session.sendline(kernel_start);

    def kernel_state (self):
        while True:
            if not self.slurm_session.isalive():
                for logline in self.slurm_session.readlines():
                    if logline.strip():
                        print(str(logline));

def slurm_jupyter_kernel ():

    parser = argparse.ArgumentParser('Adding jupyter kernels using slurm');

    parser.add_argument('connection_file', required=True);
    parser.add_argument('--cpus', help='slurm job spec: CPUs');
    parser.add_argument('--memory', help='slurm job spec: memory allocation');
    parser.add_argument('--time', required=True, help='slurm job spec: running time');
    parser.add_argument('--partition', help='slurm job spec: partition to use');
    parser.add_argument('--account', required=True, help='slurm job spec: account name');
    parser.add_argument('--reservation', help='reservation ID');
    parser.add_argument('--kernel-cmd', required=True, help='command to run jupyter kernel');

    args = parser.parse_args();

    obj_kernel = remoteslurmkernel(account=args.account,time=args.time, kernelcmd=args.kernel_cmd, connection_file=args.conecction_file, partition=args.partition, cpus=args.cpus, memory=args.memory, reservation=args.reservation);

    obj_kernel.kernel_state();
