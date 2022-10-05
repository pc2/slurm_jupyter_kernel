#!/usr/bin/python3

import argparse;
import json;
import pexpect;
import logging;
import os;
import ast;
import subprocess;

logging.basicConfig(level=logging.DEBUG);

# handle kernel as an object
class remoteslurmkernel:

    def __init__ (self, kernel_cmd, connection_file, slurm_parameter, loginnode, proxyjump, srun_cmd, environment):
        
        self.slurm_parameter = slurm_parameter;
        self.kernelcmd = kernel_cmd;
        self.slurm_session = None;
        self.connection_file = json.load(open(connection_file));
        self.loginnode = loginnode;
        if proxyjump:
            self.proxyjump = proxyjump;
        self.srun_cmd = 'srun';
        if srun_cmd:
            self.srun_cmd = srun_cmd;
        self.environment = {};
        if environment:
            # make a dict of type string to an actual dictonary
            self.environment = ast.literal_eval(environment);

        self.start_slurm_kernel();

    def start_slurm_kernel (self):
        cmd_args = [];
        default_slurm_job_name = 'jupyter_slurm_kernel';

        self.slurm_parameter = dict( (key.strip(), val.strip()) for key, val in (item.split('=') for item in self.slurm_parameter.split(',')) );
        for parameter, value in self.slurm_parameter.items():
            cmd_args.append(f'--{parameter}={value}');

        cmd_args = " ".join(cmd_args);

        # ssh cmd
        proxjump = '';
        if self.proxyjump:
            proxyjump = f'-J {self.proxyjump}';
        ssh_cmd = f'ssh -tA {proxyjump} {self.loginnode}';

        cmd = f'{ssh_cmd} {self.srun_cmd} {cmd_args} -J {default_slurm_job_name} -vu bash -i';

        logging.debug(f"Running slurm kernel command: {cmd}");
        
        self.slurm_session = pexpect.spawn(str(cmd), timeout=500);
        self.slurm_session.expect('Node (.*), .* tasks started');
        
        # get execution node
        exec_node = self.slurm_session.match.groups()[0];
        self.exec_node = exec_node.decode('utf-8');
        logging.debug(f'Slurm execution node: {self.exec_node}');

        if len(self.environment) >= 1:
            for key, val in self.environment.items():
                logging.debug(f"Send to session: export {key}={val}")
                self.slurm_session.sendline(f"export {key}={val}");
       
        if not self.slurm_session == None:
            self.kernel_connection_info = json.dumps(self.connection_file);
            logging.debug("Kernelinfo: " + str(self.kernel_connection_info));
            self.slurm_session.sendline(f"echo '{self.kernel_connection_info}' > /tmp/rkernel.json");

            self.kernelcmd = self.kernelcmd.format(remote_connection_file='/tmp/rkernel.json');

            logging.debug(f"Try to initialize kernel with command: {self.kernelcmd}");

            kernel_start = self.kernelcmd;
            self.slurm_session.sendline(kernel_start);
            self.initialize_ssh_tunnels();

    def initialize_ssh_tunnels (self):
        if not self.exec_node == None:
            port_forward = ' ';
            # following port names should be forwarded to establishing a connection to the kernel

            port_host_mapping = '127.0.0.1';
            port_forward = port_forward.join(['-L {{{kport}}}:HOST:{{{kport}}}'.format(kport=kport) for kport in [ 'stdin_port', 'shell_port', 'iopub_port', 'hb_port', 'control_port' ]]);

            # replace format keywords in port_forward with the kernel information
            port_forward = port_forward.format(**self.connection_file);
            port_forward = port_forward.replace('HOST', port_host_mapping);

            SSH_HOST = self.exec_node;
            PROXY_JUMP = '';
            if self.proxyjump:
                PROXY_JUMP = f'-J {self.proxyjump},{self.loginnode}';

            ssh_cmd = f'ssh -fNA -o StrictHostKeyChecking=no {PROXY_JUMP} {port_forward} {SSH_HOST}';

            logging.debug(f'Establishing SSH Session with command: {ssh_cmd}');

            # start SSH session with port forwarding
            subprocess.Popen(str(ssh_cmd), shell=True);
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
    parser.add_argument('--loginnode');
    parser.add_argument('--proxyjump');
    parser.add_argument('--environment');
    parser.add_argument('--srun-cmd');
    parser.add_argument('--slurm-parameter', help="Slurm job parameter")
    parser.add_argument('--kernel-cmd', required=True, help='command to run jupyter kernel');

    args = parser.parse_args();

    kernel = remoteslurmkernel(args.kernel_cmd, args.connection_file, args.slurm_parameter, args.loginnode, args.proxyjump, args.srun_cmd, args.environment);
    kernel.kernel_state();
