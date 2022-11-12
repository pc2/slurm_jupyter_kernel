import os;
import subprocess;
from pexpect import pxssh;
from shutil import copyfile;

class Color:
    # Foreground
    F_Default = "\x1b[39m"
    F_Black = "\x1b[30m"
    F_Red = "\x1b[31m"
    F_Green = "\x1b[32m"
    F_Yellow = "\x1b[33m"
    F_Blue = "\x1b[34m"
    F_Magenta = "\x1b[35m"
    F_Cyan = "\x1b[36m"
    F_LightGray = "\x1b[37m"
    F_DarkGray = "\x1b[90m"
    F_LightRed = "\x1b[91m"
    F_LightGreen = "\x1b[92m"
    F_LightYellow = "\x1b[93m"
    F_LightBlue = "\x1b[94m"
    F_LightMagenta = "\x1b[95m"
    F_LightCyan = "\x1b[96m"
    F_White = "\x1b[97m"

class WrongFileType (Exception):
    pass;
class NoEditorGiven (Exception):
    pass;
class FileAlreadyExists (Exception):
    pass;
class SSHConnectionError (Exception):
    pass;
class SSHAgentNotRunning (Exception):
    pass;
class RenderTemplateError (Exception):
    pass;

class ScriptTemplate:

    template_directory = os.path.dirname(__file__) + '/kernel_scripts';

    def __init__ (self, template=None):
        self.template = template;

    def get_all (self):
        if self.template_directory:
            return [ script for script in os.listdir(self.template_directory) if script.endswith('.sh') ];
        else:
            return False;
        
    def choose_template (self):

        script_templates = self.get_all();
        if len(script_templates) >= 1:
            id = 0;
            for script in script_templates:
                print(f'\033[94m[{id}]\033[0m {script}');
                id += 1;

            while True:
                template_to_install = input('Please choose a kernel script template to install using the \033[94midentifier\033[0m:\033[94m ');
                if template_to_install == '':
                    print(f'{Color.F_LightRed}Invalid identifier{Color.F_Default}');
                    continue;
                try:
                    template_to_install = script_templates[int(template_to_install)];
                    break;
                except IndexError:
                    print(f'{Color.F_LightRed}Kernel script template with id {template_to_install} not found!{Color.F_Default}');
                    continue;

            print('\033[0m');

            script_to_install = self.template_directory + '/' + template_to_install;
            return script_to_install;


    def use (self, loginnode=None, user=None, proxyjump=None, dry_run=False):

        ssh_options = {};
        kernel_specs = ['KERNEL_LANGUAGE', 'KERNEL_DISPLAYNAME', 'KERNEL_CMD', 'KERNEL_ENVIRONMENT'];

        # first of all: check running ssh-agent
        try:
            os.environ['SSH_AUTH_SOCK'];
        except KeyError:
            raise SSHAgentNotRunning();

        # get info to start up ssh connection
        proxy = '';
        ssh_cmd_str = '$ ssh';
        if proxyjump is None:
            if not loginnode or not user:
                proxy_represent = f'{Color.F_Cyan}-J ??????{Color.F_Default}';
                print(ssh_cmd_str + ' ' + proxy_represent);
                proxyjump = input(f'SSH Proxyjump (leave empty if not needed):{Color.F_Cyan} ');
                
                print(Color.F_Default);
                if not proxyjump == '':
                    proxy = proxyjump;
                    ssh_cmd_str += ' ' + '-J ' + proxyjump;
                    ssh_options['ProxyJump'] = proxyjump;
        else:
            proxy = proxyjump;
            ssh_cmd_str = ssh_cmd_str + ' -J ' + proxyjump;
            ssh_options['ProxyJump'] = proxyjump;
        if loginnode is None:
            loginnode_represent = f'{Color.F_Magenta}??????{Color.F_Default}';
            print(ssh_cmd_str + ' ' + loginnode_represent);
            loginnode = input(f'SSH Loginnode: {Color.F_Magenta}');
            print(Color.F_Default);
            ssh_cmd_str = ssh_cmd_str + ' ' + loginnode;
        else:
            ssh_cmd_str = ssh_cmd_str + ' ' + loginnode;
        if user is None:
            user_represent = f'{Color.F_Yellow}-l ??????{Color.F_Default}';
            print(ssh_cmd_str + ' ' + user_represent);
            user = input(f'Username for {loginnode}:{Color.F_Yellow} ');
            ssh_cmd_str = ssh_cmd_str + ' ' + user;
            print(Color.F_Default);

        # startup ssh connection
        while True:
            try:
                print(f'\nTry to establish a ssh connection using command: {Color.F_Default}{ssh_cmd_str}\n');
                ssh_session = pxssh.pxssh(options=ssh_options);
                ssh_session.login(loginnode, user);
            except pxssh.ExceptionPxssh:
                raise SSHConnectionError(f'Error: Could not establish a connection to host {loginnode}');

            # TODO: SSH Session error handling
            if not ssh_session is None:
                print(f'{Color.F_LightGreen}\u2713 Successfully established SSH session!{Color.F_Default}\n');
                break;

        if self.template:
            if self.template.endswith('.sh'):
                self.template = self.template_directory + '/' + self.template;
            else:
                self.template = self.template_directory + '/' + self.template + '.sh';

            script_to_install = self.template;
        else:
            script_to_install = self.choose_template();

        script = open(script_to_install, 'r');
        print(f'Try to parse template...');

        input_variables = {};
        set_kernel_specs = {};
        execute_lines = [];
        for line in script.readlines():
            line = line.replace('\n', '');
            if line == '' or line.startswith('#'):
                continue;

            # get all input variables
            if line.startswith('INPUT_'):
                # get everything after INPUT_* = ???
                input_variables[str(line[6])] = '='.join(line.split('=')[1:]);
            # get all kernel information
            elif line.split('=')[0] in kernel_specs:
                set_kernel_specs[str(line.split('=')[0])] = '='.join(line.split('=')[1:]);
            # and all other things: the script lines to execute
            else:
                execute_lines.append(line);

        print('\033[0m');
        # now collect input data
        var_values = {};
        for varid, inputvar in input_variables.items():
            try:
                var_value = inputvar.split(';');
                try:
                    input_default = var_value[1];
                    input_title = var_value[0];
                    tag_value = input(f'{input_title} [{input_default}]: ');
                    if tag_value == '':
                        tag_value = input_default;
                except IndexError:
                    input_title = var_value[0];
                    tag_value = input(f'{input_title}: ');

                var_values[int(varid)] = tag_value;
            except IndexError:
                print(f'Warning: Skipping line "{inputvar}" due to parsing error!');

        print('\033[0m');
        # EXECUTE ALL LINES SPECIFIED IN execute_lines
        for line in execute_lines:
            for replace_item, replace_value in var_values.items():
                if '$'+str(replace_item) in line:
                    line = line.replace('$'+str(replace_item), replace_value);
                
            if dry_run == True:
                print(f"[DRY RUN/EXECUTE TEMPLATE] Would execute: {line}");
            else:
                print(f'Executing following line: {Color.F_Blue}' + str(line) + f'{Color.F_Default}');
                ssh_session.sendline(str(line));
                ssh_session.prompt();

        # REPLACE '$' vars in kernel specs
        for type_spec, value in set_kernel_specs.items():
            for replace_item, replace_value in var_values.items():
                if '$'+str(replace_item) in value:
                    set_kernel_specs[str(type_spec)] = set_kernel_specs[str(type_spec)].replace('$'+str(replace_item), replace_value);

        ssh_session.logout();

        if len(input_variables) < 1 or len(set_kernel_specs) < 1:
            raise RenderTemplateError();

        # return kernel information
        set_kernel_specs = { key.lower(): val for key, val in set_kernel_specs.items() };
        set_kernel_specs['loginnode'] = loginnode;
        set_kernel_specs['user'] = user;
        set_kernel_specs['proxyjump'] = proxy;

        # get kernel name
        if not 'kernel_displayname' in set_kernel_specs.keys():
            set_kernel_specs['kernel_displayname'] = input(f'Display Name of the new Jupyter kernel (will be shown in e.g. JupyterLab): ');

        print('Please specify the Slurm job parameter to start the job with (comma-separated, e.g. "account=hpc,time=00:00:00"):');

        slurm_parameter = input('Slurm job parameter: ');
        set_kernel_specs['slurm_parameter'] = slurm_parameter;

        return set_kernel_specs;

    def edit (self, editor=None):

        if self.template.endswith('.sh'):
            self.template = self.template_directory + '/' + self.template;
        else:
            self.template = self.template_directory + '/' + self.template + '.sh';

        if editor is None:
            try:
                editor = os.environ['EDITOR'];
            except KeyError:
                raise NoEditorGiven(f'\033[91m$EDITOR not set. Please explicity set an editor with --editor (e.g. --editor vim)\033[0m\n');

        while True:
            edit_process = subprocess.Popen(f'{editor} {self.template}', shell=True);
            (stdout, stderr) = edit_process.communicate();
            edit_process_status = edit_process.wait();
            break;

        return True;

    @staticmethod
    def list_templates ():

        script_templates = [ template for template in os.listdir(ScriptTemplate.template_directory) if template.endswith('.sh') ];
        if len(script_templates) >= 1:
            print(f'{Color.F_LightMagenta}Following templates found:{Color.F_Default}\n');
            for template in script_templates:
                print(f'Template: {Color.F_Cyan}{template}{Color.F_Default}');
        else:
            print('No script templates found!');

    def save (self):
        
        if self.template:
            if not self.template.endswith('.sh'):
                raise WrongFileType('Wrong filetype! ".sh" needed'); 

            file_destination = self.template_directory + '/' + self.template.split('/')[:1][0];
            if os.path.isfile(file_destination):
                raise FileAlreadyExists(f'File {file_destination} already exists!');
            copyfile(self.template, file_destination);
            return True;
        else:
            raise OSError('No script template given');
