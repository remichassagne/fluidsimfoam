"""Invoke tasks to be used from the ``tasks.py`` file in the solvers"""

import hashlib
import re
from pathlib import Path
from subprocess import Popen
from time import sleep, time

import invoke.context
from invoke import task
from invoke.exceptions import Exit

from fluiddyn.util import time_as_str
from fluidsimfoam.foam_input_files import parse


def make_hex(src):
    """Produce a hash from a string"""
    return hashlib.md5(src.encode("utf8")).hexdigest()


class Context(invoke.context.Context):
    time_as_str = time_as_str()

    def run_appl(self, command, suffix_log=None):
        name_log = f"log.{command.split()[0]}"

        if suffix_log is not None:
            name_log += suffix_log

        path_log = Path(f"logs{self.time_as_str}/{name_log}")

        path_log.parent.mkdir(exist_ok=True)
        with open(path_log, "w") as file:
            self.run(command, echo=True, out_stream=file, err_stream=file)

    def run_appl_once(
        self,
        command,
        suffix_log=None,
        dict_file=None,
        check_dict_file=True,
        force=False,
    ):
        command_name = command.split()[0]

        if check_dict_file and not force:
            if dict_file is None:
                dict_file = "system/" + command_name + "Dict"

            path_dict_file = Path(dict_file)
            if not path_dict_file.exists():
                return

        lock_name = f"{command_name}_called"
        if command_name != command:
            lock_name += make_hex(command)

        path_command_called = Path(f".data_fluidsim/{lock_name}")
        path_command_called.parent.mkdir(exist_ok=True)
        if force or not path_command_called.exists():
            path_command_called.touch()
            self.run_appl(command, suffix_log=suffix_log)


invoke.tasks.Context = Context


@task
def clean(context):
    context.run("foamCleanTutorials", warn=True)
    for path in Path(".").glob(".data_fluidsim/*_called*"):
        path.unlink()


@task
def block_mesh(context):
    context.run_appl_once("blockMesh")


@task
def surface_feature_extract(context):
    context.run_appl_once("surfaceFeatureExtract")


@task
def snappy_hex_mesh(context):
    context.run_appl_once("snappyHexMesh -overwrite")


@task(pre=[block_mesh, surface_feature_extract, snappy_hex_mesh])
def polymesh(context):
    """Create the polymesh directory"""


@task
def set_fields(context, force=False):
    context.run_appl_once("setFields")


@task(pre=[polymesh, set_fields])
def run(context):
    """Main target to launch a simulation"""
    with open("system/controlDict") as file:
        ctr_dict = file.read()
    ctr_dict = parse(ctr_dict)

    application = ctr_dict.children["application"]
    end_time = ctr_dict["endTime"]
    start_time = ctr_dict["startTime"]

    path_run = Path.cwd()

    path_decompose_par_dict = path_run / "system/decomposeParDict"
    parallel = path_decompose_par_dict.exists()
    if parallel:
        context.run("decomposePar")
        nsubdoms = None
        with open(path_decompose_par_dict) as file:
            for line in file:
                if "numberOfSubdomains" in line:
                    line = line.strip().removesuffix(";")
                    nsubdoms = int(line.split()[-1])
                    break
        if nsubdoms is None:
            raise RuntimeError(f"Bad decomposeParDict {path_decompose_par_dict}")
        command = ["mpirun", "-np", str(nsubdoms), application, "-parallel"]
    else:
        command = application

    path_log = path_run / f"log_{context.time_as_str}.txt"
    print(f"Starting simulation in \n{path_run}")
    with open(path_log, "w") as file_log:
        file_log.write(f"{start_time = }\n{end_time = }\n")
        file_log.flush()
        print(f"{end_time = }")
        pattern_time = re.compile(r"\nTime = ([\d]+\.[\d]+)")
        t_start = time()
        process = Popen(command, stdout=file_log)
        t_last = time() - 10.0
        while process.poll() is None:
            sleep(0.2)
            t_now = time()
            if t_now - t_last > 2:
                t_last = t_now
                log_size = path_log.stat().st_size
                with open(path_log, "r") as file_log_read:
                    file_log_read.seek(max(0, log_size - 1000))
                    log = file_log_read.read()
                if log:
                    groups = pattern_time.findall(log)
                    if groups:
                        time_simul = float(groups[-1])
                        print(
                            f"eq_time: {time_simul:12.3f} "
                            f"({100 * time_simul/end_time:6.2f} %), "
                            f"clock_time: {t_now - t_start: 12.3f} s"
                        )

    print(f"Simulation done. path_run:\n{path_run}")
    if process.returncode:
        Exit(process.returncode)
