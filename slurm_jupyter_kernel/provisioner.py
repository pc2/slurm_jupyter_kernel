from jupyter_client.provisioning.local_provisioner import LocalProvisioner;
from jupyter_client.connect import KernelConnectionInfo;

from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from traitlets import Unicode;
from traitlets import Dict as tDict;
from time import sleep;
import re;
import json;
from subprocess import check_output, Popen, PIPE, DEVNULL, STDOUT;

# custom exceptions
class NoSlurmFlagsFound (Exception):
    pass;
class UnknownLoginnode (Exception):
    pass;
class UnknownUsername (Exception):
    pass;
class NoSlurmJobID (Exception):
    pass;
class SSHConnectionError (Exception):
    pass;

class RemoteSlurmProvisioner(LocalProvisioner):

    sbatch_flags: dict = tDict(config=True);
    proxyjump: str = Unicode(config=True);
    loginnode: str = Unicode(config=True);
    username: str = Unicode(config=True);

    default_batch_job = """#!/bin/bash
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

    def __init__(self, **kwargs):

        self.job_id = None;
        self.job_state = None;
        self.exec_node = None;
        self.active_port_forwarding = False;

        super().__init__(**kwargs);

    async def pre_launch(self, **kwargs: Any) -> Dict[str, Any]:

        if not self.sbatch_flags:
            raise NoSlurmFlagsFound('Please provide sbatch flags to start the Slurm job with!');

        if not self.loginnode:
            raise UnknownLoginnode('Could not start Slurm job. Unknown loginnode!');

        if not self.username:
            loginnode = self.loginnode;
            if self.proxyjump:
                loginnode = self.loginnode + f' (via {self.proxyjump})';
            raise UnknownUsername(f'Could not login to {loginnode}! Unknown username!');

        # Build sbatch job flags
        slurm_job_flags = '';
        for parameter, value in self.sbatch_flags.items():
            slurm_job_flags += f'#SBATCH --{parameter}={value}\n';

        # build ssh command
        proxyjump = '';
        if self.proxyjump:
            proxyjump = f'-J {self.proxyjump}';
        self.ssh_command = f'ssh -tA {proxyjump} {self.loginnode}';

        # build sbatch command
        self.sbatch_command = ['/bin/bash', '--login', '-c', '"sbatch --parsable"'];

        # add extra environment variables into sbatch job
        extra_environment = '';
        try:
            if len(self.kernel_spec.env) >= 1:
                for key, val in self.kernel_spec.env.items():
                    extra_environment += f'export {key}={val}\n';
        except:
            pass;

        # finally build the Slurm sbatch job
        kernel_command = ' '.join(self.kernel_spec.argv);
        self.batch_job = self.default_batch_job.format(SBATCH_JOB_FLAGS=slurm_job_flags,EXTRA_ENVIRONMENT=extra_environment,COMMAND=kernel_command,KERNEL_CONNECTION_INFO='{KERNEL_CONNECTION_INFO}');

        return await super().pre_launch(**kwargs)

    async def launch_kernel (self, cmd: List[str], **kwargs: Any) -> KernelConnectionInfo:

        # kernel connection info is now available - add it to the Slurm batch job
        kernel_connection_info = {};
        # the kernel connection info contains byte-strings which are not JSON valid
        for key, val in self.connection_info.items():
            if isinstance(val, bytes):
                kernel_connection_info[key] = val.decode('utf-8');
            else:
                kernel_connection_info[key] = val;

        kernel_connection_info = str(kernel_connection_info).replace("'", '"');

        self.batch_job = self.batch_job.format(KERNEL_CONNECTION_INFO=kernel_connection_info, connection_file='$connection_file');
        self.log.debug('Final sbatch jobfile: ' + str(self.batch_job));

        run_command = self.ssh_command.split(' ') + self.sbatch_command;
        self.log.debug('Would run SSH command: ' + str(run_command));

        self.process = Popen(run_command, stdout=PIPE, stderr=DEVNULL, stdin=PIPE);
        child_process_out, child_process_err = self.process.communicate(input=self.batch_job.encode());
        child_process_out = child_process_out.decode('utf-8').strip();

        self.log.debug('Submitted Slurm job! sbatch output: ' + str(child_process_out));

        # now parsing the output to fetch the Slurm job id
        self.job_id = re.search(r"(\d+)", child_process_out, re.IGNORECASE);
        if self.job_id:
            try:
                self.job_id = self.job_id.group(1);
                self.job_id = int(self.job_id);
                self.log.info("Slurm job successfully submitted. Slurm job id: " + str(self.job_id));
            except:
                raise NoSlurmJobID("Could not fetch the Slurm job id!");

        return self.connection_info;

    def _start_ssh_port_forwarding (self):

        if self.exec_node:
            if self.connection_info:

                port_forward = ' ';
                port_forward = port_forward.join(['-L {{{kport}}}:127.0.0.1:{{{kport}}}'.format(kport=kport) for kport in [ 'stdin_port', 'shell_port', 'iopub_port', 'hb_port', 'control_port' ]]);
                # replace needed ports
                port_forward = port_forward.format(**self.connection_info);

                proxy_jump = '';
                if self.proxyjump:
                    proxy_jump = f'-J {self.proxyjump},{self.loginnode}';
                else:
                    proxy_jump = f'-J {self.loginnode}';

                ssh_command = ['ssh', '-fNA', '-o', 'StrictHostKeyChecking=no'] + proxy_jump.split(' ') + port_forward.split(' ');
                ssh_command.append(self.exec_node);

                self.log.info('Starting SSH tunnel to forward kernel ports to localhost');
                self.log.debug('Using command: ' + str(ssh_command));

                ssh_tunnel_process = Popen(ssh_command, stdout=PIPE, stderr=STDOUT);
                # TODO: work with exceptions
                self.active_port_forwarding = True;

    def _get_slurm_job_state (self, job_id: int):

        check_command = self.ssh_command.split(' ') + ['-T', '/bin/bash', '--login', '-c', f'"squeue -h -j {self.job_id} -o \'%T %B\' 2> /dev/null"'];

        squeue_output = check_output(check_command);
        squeue_output = squeue_output.decode('utf-8').split(' ');
        self.state = squeue_output[0].strip();

        if 'RUNNING' in self.state:
            self.exec_node = squeue_output[1];
            self.exec_node = self.exec_node.strip();

        return [self.state, self.exec_node];

    async def poll(self) -> Optional[int]:

        # 0 = polling
        result = 0;
        if self.job_id:            
            state, exec_node = self._get_slurm_job_state(self.job_id);
            if state == 'RUNNING':
                
                if isinstance(exec_node, str):
                    if self.active_port_forwarding == False:
                        self.log.info(f'Slurm job is in state running on compute node {exec_node}');
                        self._start_ssh_port_forwarding();
                    result = None;

        return result;

    def get_shutdown_wait_time(self, recommended: float = 5) -> float:

        #recommended = 30.0;
        return super().get_shutdown_wait_time(recommended);

    def get_stable_start_time(self, recommended: float = 10) -> float:

        recommended = 30.0;
        return super().get_stable_start_time(recommended)

    async def send_signal(self, signum: int) -> None:

        if signum == 0:
            return await self.poll();
        else:
            return await super().send_signal(signum);