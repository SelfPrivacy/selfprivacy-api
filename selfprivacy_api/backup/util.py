import subprocess


def output_yielder(command):
    with subprocess.Popen(
        command,
        shell=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
    ) as handle:
        for line in iter(handle.stdout.readline, ""):
            if "NOTICE:" not in line:
                yield line
