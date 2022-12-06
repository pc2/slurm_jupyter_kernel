#!/usr/bin/python3

import argparse;
import json;
import logging;
import os;
import re;
import ast;
import subprocess;
import threading;
import time;
from threading import Thread;
from subprocess import check_output;

logging.basicConfig(level=logging.DEBUG);

# handle kernel as an object
class remoteslurmkernel:

    cmd_slurm_get_state = 'squeue -j {job_id} -ho "%T"';
    default_sbatch_job = """#!/bin/bash
#SBATCH -J jupyter_slurm_kernel
{SBATCH_JOB_FLAGS}

tmpfile=$(mktemp)
cat << EOF > $tmpfile
{KERNEL_CONNECTION_INFO}
EOF
connection_file=$tmpfile

{EXTRA_ENVIRONMENT}

{COMMAND}    
""";

    def __init__ (self, kernel_cmd, connection_file, slurm_parameter, loginnode, proxyjump, srun_cmd, environment):
        
        self.slurm_parameter = slurm_parameter;
        self.kernelcmd = kernel_cmd;
        self.slurm_session = None;
        self.job_id = None;
        self.exec_node = None;
        self.connection_file = json.load(open(connection_file));
        self.loginnode = loginnode;
        self.proxyjump = False;
        self.state = 'unknown';
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

        self.slurm_parameter = dict( (key.strip(), val.strip()) for key, val in (item.split('=') for item in self.slurm_parameter.split(',')) );
        for parameter, value in self.slurm_parameter.items():
            cmd_args.append(f'#SBATCH --{parameter}={value}');

        cmd_args = '\n'.join(cmd_args);

        # ssh cmd
        proxyjump = '';
        if self.proxyjump:
            proxyjump = f'-J {self.proxyjump}';
        self.ssh_cmd = f'ssh -A {proxyjump} {self.loginnode}';

        self.sbatch_cmd = ['/bin/bash', '--login', '-c', '"sbatch --parsable"'];

        # add extra environment variables
        extra_environment = '';
        if len(self.environment) >= 1:
            for key, val in self.environment.items():
                extra_environment += f'export {key}={val}\n';
        else:
            logging.debug('[SLURM JOB DEBUG] Do not add extra environment variables - Nothing found');

        # build batchfile
        self.kernel_connection_info = json.dumps(self.connection_file);
        self.kernelcmd = self.kernelcmd.format(remote_connection_file='$connection_file');
        batchfile = self.default_sbatch_job.format(SBATCH_JOB_FLAGS=cmd_args, KERNEL_CONNECTION_INFO=self.kernel_connection_info, EXTRA_ENVIRONMENT=extra_environment, COMMAND=self.kernelcmd);

        run_command = self.ssh_cmd.split(' ') + self.sbatch_cmd;
        sbatch_process = subprocess.Popen(run_command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, stdin=subprocess.PIPE);
        sbatch_out, sbatch_err = sbatch_process.communicate(input=batchfile.encode());
        sbatch_out = sbatch_out.decode('utf-8');

        logging.debug(f'[SLURM JOB DEBUG] sbatch command output: ' + str(sbatch_out));

        self.job_id = re.search(r"(\d+)", sbatch_out, re.IGNORECASE);
        if self.job_id:
            try:
                self.job_id = self.job_id.group(1);
                self.job_id = int(self.job_id);
                logging.info(f'[SLURM JOB UPDATE] Extracted Slurm job id: {self.job_id}');
            except ValueError:
                logging.error(f'[SLURM JOB ERROR] The extracted job id -> {self.job_id} <- does not seem to be an integer!');
                raise ValueError(f'[SLURM JOB ERROR] The extracted job id -> {self.job_id} <- does not seem to be an integer!');

        # Check Slurm job state
        # return function if Slurm job state is RUNNING
        slurm_job_state = self.check_slurm_job();
        if slurm_job_state:
            port_forwarding_t = threading.Thread(target=self.initialize_ssh_tunnels);
            port_forwarding_t.start();

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

            ssh_cmd = f'ssh -A -o StrictHostKeyChecking=no {PROXY_JUMP} {port_forward} {SSH_HOST}';

            logging.debug(f'[SLURM JOB UPDATE] Establishing SSH Session with command: {ssh_cmd}');

            # start SSH session with port forwarding
            # We need shell=True to provide the SSH environment (agent, loaded keys, ...)
            ssh_tunnel_process = subprocess.Popen(ssh_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True);
            tunnel_proc_stdout, tunnel_proc_stderr = ssh_tunnel_process.communicate();

        else:
            logging.error('[SLURM JOB ERROR] Cannot forward kernel ports! Execution node unknown!');

    def check_slurm_job (self):

        if not self.cmd_slurm_get_state is None:
            if self.job_id:
                self.cmd_slurm_get_state = self.cmd_slurm_get_state.format(job_id=self.job_id);

                check_command = self.ssh_cmd.split(' ') + ['-T', '/bin/bash', '--login', '-c', f'"squeue -h -j {self.job_id} -o \'%T %B\' 2> /dev/null"'];

                while True:
                    time.sleep(4);
                    squeue_output = check_output(check_command);
                    squeue_output = squeue_output.decode('utf-8').split(' ');
                    self.state = squeue_output[0];

                    if 'PENDING' in self.state:
                        logging.debug('Jupyter Slurm job is in state PENDING');
                        continue;
                    elif 'RUNNING' in self.state:
                        logging.info('[SLURM JOB UPDATE] Jupyter Slurm job is now in state RUNNING! Try getting execution node...');
                        try:
                            self.exec_node = squeue_output[1];
                        except IndexError:
                            squeue_output = ' '.join(squeue_output);
                            logging.error(f'[SLURM JOB ERROR] Could not fetch the Slurm execution node from output -> {squeue_output} <- Cannot forward remote kernel ports!');

                        if self.exec_node:
                            logging.info(f'[SLURM JOB UPDATE] Execution node: {self.exec_node}');
                        else:
                            logging.error(f'Failed to get execution node using following squeue output: {squeue_output}');

                        return True;
                    else:
                        logging.error("Jupyter Slurm job is neither PENDING nor RUNNING?");
                        continue;

        else:
            raise NotImplementedError('Specify remoteslurmkernel.cmd_slurm_get_state to fetch slurm job state!');

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
    remoteslurmkernel(args.kernel_cmd, args.connection_file, args.slurm_parameter, args.loginnode, args.proxyjump, args.srun_cmd, args.environment);
