#pylint: disable=C0103
"""
class for executing NASMAT problems
"""
import os
import sys
import subprocess
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from util.npp_settings import get_npp_settings #pylint: disable=C0413


class NASMAT(): #pylint: disable=C0103
    """
    NASMAT - executes a NASMAT analysis from a *.MAC file
    """
    def __init__(self,solver,h5path,intel_path='',intel_options='',clean_cmd=False):
        """
        initialize class

        Parameters:
            solver (str): name of the NASMAT exectuable file
            h5path (str): location of the hdf5.dll file 
                          [e.g., $hdf5_install_directory/bin]
            intel_path (str): location of setvars.bat (OneAPI) or ifortvars.bat (older compilers) 
                              file in Intel installation directory. This requires python be run 
                              from a command prompt and not from a powershell.
                              Add "terminal.integrated.defaultProfile.windows": "Command Prompt" 
                              to settings.json file in VS Code to change default.
            intel_options (str): space-delimeted str of intel options to pass to 
                                 intel_path *.bat file (e.g., "intel64 vs2022")
            clean_cmd (bool): flag to overwrite current OS environment with clean one

        Returns:
            None.
        """

        #setup NASMAT environment
        self.solver=solver
        self.h5path=h5path
        self.intel_path=intel_path
        self.intel_options=intel_options

        if clean_cmd:
            env={"PATH":''}
        else:
            env = os.environ.copy()

        if h5path:
            new_path = h5path + env["PATH"] #Windows convention
            env["PATH"]=new_path
        # print(new_path)
        self.env=env
        self.echo = False
        self.mac=None
        self.proc = None
        self._setup_env()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._cleanup()

    def _cleanup(self):
        """
        function for cleaning up after NASMAT is run

        Parameters:
            None.

        Returns:
            None.
        """

        if self.proc:
            try:
                if self.proc.stdin:
                    self.proc.stdin.close()
                if self.proc.stdout:
                    self.proc.stdout.close()
                if self.proc.stderr:
                    self.proc.stderr.close()
                self.proc.wait()
            except Exception as e: #pylint: disable=W0718
                print(f"Error during cleanup: {e}")
            finally:
                self.proc = None

    def _setup_env(self):

        self.proc = subprocess.Popen(['cmd.exe'], stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if self.intel_path or self.intel_options:
            run_cmd = f'"{self.intel_path}" {self.intel_options} >nul 2>&1\n'
            self.proc.stdin.write(run_cmd)

        self.proc.stdin.write("echo Setup complete\n")
        self.proc.stdin.flush()

        while True:
            output = self.proc.stdout.readline()
            if "Setup complete" in output:
                break


    def run(self,mac,echo=True):
        """
        function for executing NASMAT

        Parameters:
            mac (str): mac file to execute
            echo (bool): flag to print to screen

        Returns:
            None.
        """

        self.echo=echo
        if not isinstance(mac, list):
            self.mac=[mac]
        else:
            self.mac=mac
        #solver_cmd = self.solver + ' ' + mac
        #run_cmd = f'"{self.intel_path}" {self.intel_options} >nul 2>&1 && {solver_cmd}'
        #run_cmd = solver_cmd #Testing
        #self._call_subprocess(run_cmd) #this works, but requires intel path to be set each time
        self._run_nasmat()

    def _run_nasmat(self):
        """
        function for executing NASMAT

        Parameters:
            None.

        Returns:
            None.
        """

        for m in self.mac:
            solver_cmd = self.solver + f" {m}\n"
            self.proc.stdin.write(solver_cmd)
            self.proc.stdin.flush()

        self.proc.stdin.close()

        if self.echo:
            for line in self.proc.stdout:
                print(line, end='')

        self.proc.wait()

        if self.proc.returncode != 0:
            print("An error occurred while setting up the environment or running NASMAT.")
        else:
            print("NASMAT executed successfully.")


    def _call_subprocess(self,run_cmd):
        """
        function for calling subprocess commands (not used)

        Parameters:
            run_cmd (str): run command to execute

        Returns:
            None.
        """

        try:
            result = subprocess.run(run_cmd, stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE, text=True,
                                     env=self.env, check=True,shell=True)
            if self.echo:
                print("Output:", result.stdout)
        except subprocess.CalledProcessError as e:
            print("Output:", e.stdout)
            print("Error:", e.stderr)
            print("Exit code:", e.returncode)
        except Exception as e:
            raise Exception(f"An unexpected error occurred:{e}") #pylint: disable=W0707,W0719

if __name__ == "__main__":

    npps=get_npp_settings(echo=True)
    if npps:
        sol = npps['NASMAT_SOLVER']
        h5p = npps['HDF5_PATH']
        intel_p = npps['INTEL_PATH']
        intel_opts = npps['INTEL_OPTS']
    else:
        intel_p = r"C:\Program Files (x86)\Intel\oneAPI\setvars.bat"
        intel_opts = "intel64 vs2022"
        h5p=r"C:\HDF_Group\1.14.3\bin;"
        sol=r'C:\Users\tmricks\source\Workspaces\NASMAT_v500\Executable\NASMAT_SP_WIN.exe'

    nasmat=NASMAT(sol,h5p,intel_p,intel_opts)
    nasmat.run(mac=".\\NASMAT\\TEST1.MAC")
