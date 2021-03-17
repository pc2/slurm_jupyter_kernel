#!/usr/bin/python3

import argparse;
import json;
import pexpect;
import logging;
import re;
import os;

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
        self.ssh_port = 22;
        self.connection_file = json.load(open(connection_file));

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
        self.slurm_session.expect('srun: Node (.*), .* tasks started');
        
        # get execution node
        exec_node = self.slurm_session.match.groups()[0];
        self.exec_node = exec_node.decode('utf-8');
        logging.debug(f'SLURM Execution node: {self.exec_node}');
       
        if not self.slurm_session == None:
            self.kernel_connection_info = json.dumps(self.connection_file);
            self.slurm_session.sendline(f'echo {self.kernel_connection_info} > kernel.json');

            logging.debug(f"Try to initialize kernel with command: {self.kernelcmd}");

            kernel_start = self.kernelcmd;
            self.slurm_session.sendline(kernel_start);
            self.initialize_ssh_tunnels();

    def initialize_ssh_tunnels (self):
        if not self.exec_node == None:
            port_forward = ' ';
            # following port names should be forwarded to establishing a connection to the kernel
            port_forward = port_forward.join(['-L {{{kport}}}:127.0.0.1:{{{kport}}}'.format(kport=kport) for kport in [ 'stdin_port', 'shell_port', 'iopub_port', 'hb_port', 'control_port' ]]);

            # replace format keywords in port_forward with the kernel information
            port_forward = port_forward.format(**self.connection_file);

            ssh_cmd = f'ssh {port_forward} {self.exec_node}';
            logging.debug(f'Establishing SSH Session with command: {ssh_cmd}');

            # start SSH session with port forwarding
            # The user should have access to 'self.exec_node' because there is already a SLURM job running
            ssh_tunnel_connection = pexpect.spawn(str(ssh_cmd), timeout=500);
        else:
            logging.debug('self.exec_host is type NONE');

    def kernel_state (self):
        while True:
            if not self.slurm_session.isalive():
                for logline in self.slurm_session.readlines():
                    if logline.strip():
                        logging.debug(str(logline));

def slurm_jupyter_kernel ():

    parser = argparse.ArgumentParser('Adding jupyter kernels using slurm');

    parser.add_argument('--connection-file');
    parser.add_argument('--cpus', help='slurm job spec: CPUs');
    parser.add_argument('--memory', help='slurm job spec: memory allocation');
    parser.add_argument('--time', required=True, help='slurm job spec: running time');
    parser.add_argument('--partition', help='slurm job spec: partition to use');
    parser.add_argument('--account', required=True, help='slurm job spec: account name');
    parser.add_argument('--reservation', help='reservation ID');
    parser.add_argument('--kernel-cmd', required=True, help='command to run jupyter kernel');

    args = parser.parse_args();

    obj_kernel = remoteslurmkernel(account=args.account,time=args.time, kernelcmd=args.kernel_cmd, connection_file=args.connection_file, partition=args.partition, cpus=args.cpus, memory=args.memory, reservation=args.reservation);

    obj_kernel.kernel_state();
