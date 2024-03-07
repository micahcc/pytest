import glob
import os
from subprocess import Popen, PIPE, STDOUT
from typing import Union
from enum import Enum
import string
import random
from typing import Any, Callable, Dict, List, Optional, Tuple
import shlex
import base64
import time

BASH_EXE = "/run/current-system/sw/bin/bash"


class LOG_TYPE(Enum):
    Info = (0,)
    Warning = (1,)
    Error = (2,)
    Critical = 3


class BashInteractive:
    def __init__(self, source: str) -> None:
        super().__init__()
        mod_env = os.environ.copy()

        self.base = Popen(
            source,
            stdin=PIPE,
            stdout=PIPE,
            stderr=STDOUT,
            text=True,
            shell=True,
            close_fds=True,
            env=mod_env,
        )

    def cli_alive(self) -> Union[bool, int]:
        if self.base.poll() is None:
            return True
        else:
            return False

    def pid(self) -> int:
        return self.base.pid

    def terminate(self) -> None:
        if self.cli_alive():
            self.base.stdin.write("exit")
            self.base.stdin.flush()
            self.base.terminate()

    def execute(
        self,
        command: str,
        check_return: bool = True,
        timeout: Optional[int] = 60,
        text=False,
    ) -> Tuple[int, Union[bytes, str]]:
        if not self.cli_alive():
            print("Not alive")
            return -1, ""

        command = command.strip()

        # we'll only produce stdout
        if command.endswith("&"):
            command = command[0:-1] + "2>&1 &"
        else:
            command += " 2>&1"
        if timeout is not None:
            command = "timeout {} sh -c {}".format(timeout, shlex.quote(command))
        command = f"( set -euo pipefail; {command} ) | (base64 --wrap 0; echo; echo;)\n"

        print(f"Executing: {command}")
        self.base.stdin.write(command)
        self.base.stdin.flush()

        # Get the output
        # we end with two echo (\n\n), base64 won't produce that, so we can safely
        # wait until we get an empty line
        stdout = ""
        line = ""
        while line != "\n":
            if self.base.stdout.readable():
                line = self.base.stdout.readline()
                stdout += line

        output = base64.b64decode(stdout)

        # Get the return code
        self.base.stdin.write("echo $?\n")
        self.base.stdin.flush()
        statuscode_str = self.base.stdout.readline().strip()
        statuscode = int(statuscode_str)

        if text:
            result = (statuscode, output.decode())
        else:
            result = (statuscode, output)
        print(f"Result: {result}")
        return result


def main():
    cli = BashInteractive(source=BASH_EXE)
    ret, stderr = cli.execute(
        command="file C:/Windows/system32/win32calc.exe", text=True
    )
    ret, stderr = cli.execute(command="echo hello", text=True)
    ret, stderr = cli.execute(command="env", text=True)
    ret, stderr = cli.execute(command="dd if=/dev/urandom bs=3 count=1")


if __name__ == "__main__":
    main()
