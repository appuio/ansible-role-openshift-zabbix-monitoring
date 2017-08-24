#!/usr/bin/env python
#     ___ ___ _  _ ___ ___    _ _____ ___ ___
#    / __| __| \| | __| _ \  /_\_   _| __|   \
#   | (_ | _|| .` | _||   / / _ \| | | _|| |) |
#    \___|___|_|\_|___|_|_\/_/_\_\_|_|___|___/_ _____
#   |   \ / _ \  | \| |/ _ \_   _| | __|   \_ _|_   _|
#   | |) | (_) | | .` | (_) || |   | _|| |) | |  | |
#   |___/ \___/  |_|\_|\___/ |_|   |___|___/___| |_|
"""Run an ssh agent and set SSH_AUTH_SOCK so that clients will use it

Example:
    with ssh_agent.SshAgent() as agent:
        agent.add_key(private_key_string)
        # do ssh stuff
    # as agent loses scope, the ssh agent is killed
"""

from __future__ import with_statement
import atexit
import tempfile
import os
import sys
import shutil
import subprocess
import random
import time
import datetime

class SshAgentException(Exception):
    """An exception thrown for problems in SshAgent
    """
    def __init__(self, message):
        # Call the base class constructor with the parameters it needs
        super(SshAgentException, self).__init__(message)

class SshAgent(object):
    """Run an ssh agent and set SSH_AUTH_SOCK so that clients will use it.

    The running agent can have one or more keys added (via the SshAgent.add_key()
    method or via any other method that can find and talk to the running agent.
    """

    class Cleanup(object):
        """A helper functor class for SshAgent

        An object of this class can be passed
        directly to atexit, which will call __call__() when the
        program exits
        """
        def __init__(self, ssh_agent, ssh_auth_sock_dir):
            self.ssh_agent = ssh_agent
            self.ssh_auth_sock_dir = ssh_auth_sock_dir
            self.cleaned_up = False
            self.original_env_var = os.environ.get('SSH_AUTH_SOCK')
        def __call__(self):
            if self.cleaned_up:
                return
            self.cleaned_up = True
            try:
                shutil.rmtree(self.ssh_auth_sock_dir, ignore_errors=True)
            except OSError:
                pass
            try:
                self.ssh_agent.kill()
            except OSError:
                pass
            if self.original_env_var:
                os.environ['SSH_AUTH_SOCK'] = self.original_env_var
            else:
                del os.environ['SSH_AUTH_SOCK']
        def pass_(self):
            """A function to appease pylint"""
            pass
        def pass__(self):
            """Another function to appease pylint"""
            self.pass_()
    def __init__(self):
        devnull = open(os.devnull, 'w')
        # Start an ssh-agent process and register it to be killed atexit
        self.ssh_auth_sock_dir = tempfile.mkdtemp(prefix=os.path.basename(sys.argv[0]) + '.')
        self.ssh_auth_sock = os.path.join(self.ssh_auth_sock_dir, "ssh_agent")
        self.ssh_agent = subprocess.Popen(["ssh-agent", "-d", "-a", self.ssh_auth_sock], stdout=devnull, stderr=devnull)
        self.cleanup = self.Cleanup(self.ssh_agent, self.ssh_auth_sock_dir)
        # this is here so that when python exits, we make sure that the agent is killed
        # (in case python exits before our __del__() is called
        atexit.register(self.cleanup)
        os.environ["SSH_AUTH_SOCK"] = self.ssh_auth_sock
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_value, tback):
        self.cleanup()
    def __del__(self):
        self.cleanup()

    def kill(self):
        '''Explicitly kill the running ssh-agent

        It's not necessary to call this function as the agent
        will be cleaned up automatically.
        '''
        self.cleanup()

    def add_key(self, key):
        """Add a key to the running agent.

        Note:
            This function can be called any number of times to add multiple keys.

        Args:
            key (str): A string containing the ssh private key to be added (the
                    actual key data, not the filename of a key)
        Raises:
            SshAgentException: when ssh-add does not immediately return (as in the
                    case of a private key with a passphrase)
        """
        #if self.ssh_agent.poll() is None:
        #    raise SshAgentException("Unable to add ssh key. Did agent die?")
        named_pipe_path = os.path.join(self.ssh_auth_sock_dir, "keypipe." + str(random.getrandbits(64)))
        try:
            os.mkfifo(named_pipe_path, 0600)
        except OSError, exception:
            print "Failed to create FIFO: %s" % exception
        devnull = open(os.devnull, 'w')
        ssh_add = subprocess.Popen(["ssh-add", named_pipe_path], stdout=devnull, stderr=devnull)
        fifo = open(named_pipe_path, 'w')
        print >> fifo, key
        fifo.close()
        #Popen.wait() doesn't have a timeout, so we'll implement one using poll() :(
        start_time = datetime.datetime.now()
        while ssh_add.poll() is None:
            if (datetime.datetime.now() - start_time).total_seconds() > 5:
                try:
                    ssh_add.kill()
                except OSError:
                    pass
                raise SshAgentException("Unable to add ssh key. Timed out. Does key have a passphrase?")
            time.sleep(0.1)
        os.remove(named_pipe_path)
# pylint: disable=too-many-lines

# these are already imported inside of the ssh library
#import os
#import subprocess

class GitCLIError(Exception):
    '''Exception class for openshiftcli'''
    pass

# pylint: disable=too-few-public-methods
class GitCLI(object):
    ''' Class to wrap the command line tools '''
    def __init__(self,
                 path,
                 verbose=False,
                 ssh_key=None,
                 author=None):
        ''' Constructor for GitCLI '''
        self.path = path
        self.verbose = verbose
        self.ssh_key = ssh_key
        self.author = author
        self.environment_vars = os.environ.copy()

        if self.author:
            author_dict = {}
            author_list = author.split('<')
            author_dict['GIT_COMMITTER_NAME'] = author_list[0].strip()
            author_dict['GIT_COMMITTER_EMAIL'] = author_list[0].strip()

            self.environment_vars.update(author_dict)

    def _add(self, files_to_add=None):
        ''' git add '''

        cmd = ["add", "--no-ignore-removal"]

        if files_to_add:
            cmd.extend(files_to_add)
        else:
            cmd.append('.')

        results = self.git_cmd(cmd)

        return results

    def _commit(self, msg, author=None):
        ''' git commit with message '''

        cmd = ["commit", "-m", msg]

        if author:
            cmd += ["--author", author]

        results = self.git_cmd(cmd)

        return results

    def _clone(self, repo, dest, bare=False):
        ''' git clone '''

        cmd = ["clone"]

        if bare:
            cmd += ["--bare"]

        cmd += [repo, dest]

        results = self.git_cmd(cmd)

        return results

    def _fetch(self, remote):
        ''' git fetch '''

        cmd = ["fetch"]

        cmd += [remote]

        results = self.git_cmd(cmd, output=True, output_type='raw')

        return results

    def _status(self, porcelain=False, show_untracked=True):
        ''' Do a git status '''

        cmd = ["status"]
        if porcelain:
            cmd.append('--porcelain')

        if show_untracked:
            cmd.append('--untracked-files=normal')
        else:
            cmd.append('--untracked-files=no')

        results = self.git_cmd(cmd, output=True, output_type='raw')

        return results

    def _checkout(self, branch):
        ''' Do a git checkout to <branch> '''

        cmd = ["checkout", branch]
        results = self.git_cmd(cmd, output=True, output_type='raw')

        return results

    def _get_current_branch(self):
        ''' Do a git checkout to <branch> '''

        cmd = ["describe", "--contains", "--all", "HEAD"]
        results = self.git_cmd(cmd, output=True, output_type='raw')
        results['results'] = results['results'].rstrip()

        return results

    def _merge(self, merge_id):
        ''' Do a git checkout to <branch> '''

        cmd = ["merge", merge_id]
        results = self.git_cmd(cmd, output=True, output_type='raw')

        return results

    def _push(self, remote, src_branch, dest_branch):
        ''' Do a git checkout to <branch> '''

        push_branches = src_branch + ":" + dest_branch

        cmd = ["push", remote, push_branches]
        results = self.git_cmd(cmd, output=True, output_type='raw')

        return results

    def _remote_update(self):
        ''' Do a git remote update '''

        cmd = ["remote", "update"]
        results = self.git_cmd(cmd, output=True, output_type='raw')

        return results

    def _diff(self, diff_branch):
        ''' Do a git diff diff_branch'''

        cmd = ["diff", diff_branch]
        results = self.git_cmd(cmd, output=True, output_type='raw')

        return results

    def _rebase(self, rebase_branch):
        ''' Do a git rebase rebase_branch'''

        cmd = ["rebase", rebase_branch]
        results = self.git_cmd(cmd, output=True, output_type='raw')

        return results

    def _config(self, get_args):
        ''' Do a git config --get <get_args> '''

        cmd = ["config", '--get', get_args]
        results = self.git_cmd(cmd, output=True, output_type='raw')

        return results

    def git_cmd(self, cmd, output=False, output_type='json'):
        '''Base command for git '''
        cmds = ['/usr/bin/git']

        cmds.extend(cmd)

        rval = {}
        results = ''
        err = None

        if self.verbose:
            print ' '.join(cmds)

        if self.ssh_key:
            with SshAgent() as agent:
                self.environment_vars['SSH_AUTH_SOCK'] = os.environ['SSH_AUTH_SOCK']
                agent.add_key(self.ssh_key)

                proc = subprocess.Popen(cmds,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                                        env=self.environment_vars)

                stdout, stderr = proc.communicate()

                rval = {"returncode": proc.returncode,
                        "results": results,
                        "cmd": ' '.join(cmds),
                       }
        else:
            proc = subprocess.Popen(cmds,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    env=self.environment_vars)

            stdout, stderr = proc.communicate()
            rval = {"returncode": proc.returncode,
                    "results": results,
                    "cmd": ' '.join(cmds),
                   }


        if proc.returncode == 0:
            if output:
                if output_type == 'json':
                    try:
                        rval['results'] = json.loads(stdout)
                    except ValueError as err:
                        if "No JSON object could be decoded" in err.message:
                            err = err.message
                elif output_type == 'raw':
                    rval['results'] = stdout

            if self.verbose:
                print stdout
                print stderr

            if err:
                rval.update({"err": err,
                             "cmd": cmds
                            })

        else:
            rval.update({"results": {}})

        # Always include stdout/stderr:
        rval.update({"stderr": stderr,
                     "stdout": stdout})

        return rval

class GitFetch(GitCLI):
    ''' Class to wrap the git merge line tools '''
    # pylint: disable=too-many-arguments
    def __init__(self,
                 path,
                 remote,
                 ssh_key=None):
        ''' Constructor for GitFetch '''
        super(GitFetch, self).__init__(path, remote, ssh_key=ssh_key)
        self.remote = remote
        self.debug = []

        if not os.path.isdir(self.path):
            print "Git checkout directory does not exist. Exiting..."
            sys.exit(1)

    def fetch(self):
        ''' fetch from the selected remote '''

        os.chdir(self.path)

        fetch_results = self._fetch(self.remote)
        no_fetch_needed = False

        # TODO: Check for no results
        if fetch_results['returncode'] != 0:
            return {'returncode': 1,
                    'results': fetch_results,
                    'error_msg': 'Unable to fetch for remote: ' + self.remote,
                    'no_fetch_needed': False
                   }

        # git fetch returns output to stderr.
        # Success but no stderr contents implies nothing was fetched.
        no_fetch_needed = len(fetch_results['stderr']) == 0
        return {'returncode': 0,
                'results': fetch_results,
                'no_fetch_needed': no_fetch_needed
               }


def main():
    '''
    ansible git module for cloning
    '''
    module = AnsibleModule(
        argument_spec=dict(
            # TODO: state necessary for this?
            state=dict(default='present', type='str', choices=['present']),
            path=dict(default=None, required=True, type='str'),
            remote=dict(default='origin', required=False, type='str'),
            ssh_key=dict(default=None, required=False, type='str'),
        ),
        supports_check_mode=False,
    )
    git = GitFetch(module.params['path'],
                   module.params['remote'],
                   module.params['ssh_key'])

    state = module.params['state']

    if state == 'present':
        results = git.fetch()

        if results['returncode'] != 0:
            module.fail_json(msg=results)

        if results['no_fetch_needed'] == True:
            module.exit_json(changed=False, results=results, state="present")

        module.exit_json(changed=True, results=results, state="present")

    module.exit_json(failed=True,
                     changed=False,
                     results='Unknown state passed. %s' % state,
                     state="unknown")

# pylint: disable=redefined-builtin, unused-wildcard-import, wildcard-import, locally-disabled
# import module snippets.  This are required
if __name__ == '__main__':
    from ansible.module_utils.basic import *
    main()
