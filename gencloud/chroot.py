import os
import sys
from subprocess import Popen, PIPE
import gencloud.config

def bind(mount=gencloud.config.GENTOO_MOUNT, verbose=True):
    mounts = [
        ["mount", "--types", "proc", "/proc", os.path.join(mount, "proc")],
        ["mount", "--rbind", "/sys", os.path.join(mount, "sys")],
        ["mount", "--make-rslave", os.path.join(mount, "sys")],
        ["mount", "--rbind", "/dev", os.path.join(mount, "dev")],
        ["mount", "--make-rslave", os.path.join(mount, "dev")],
        ["mount", "--bind", "/run", os.path.join(mount, "run")],
        ["mount", "--make-slave", os.path.join(mount, "run")],
    ]
    for mcmd in mounts:
        if verbose:
            print(f"\t:: {' '.join(mcmd)}")
        proc = Popen(mcmd, stdout=PIPE, stderr=PIPE)
        stdout, stderr = proc.communicate()
        if proc.returncode != 0:
            sys.stderr.write(f"{stderr}\n")
            sys.exit(proc.returncode)

def unbind(mount=gencloud.config.GENTOO_MOUNT, verbose=True):
    unmounts = [
        ["umount", "-l", os.path.join(mount, 'dev', 'shm')],
        ["umount", "-l", os.path.join(mount, 'dev', 'pts')],
        ["umount", "-R", mount]
    ]
    os.chdir("/")
    for uncmd in unmounts:
        if verbose:
            print(f"\t:: {' '.join(uncmd)}")
        proc = Popen(uncmd, stdout=PIPE, stderr=PIPE)
        stdout, stderr = proc.communicate()
        if proc.returncode != 0:
            sys.stderr.write(f"{stderr}\n")
            sys.exit(proc.returncode)

def chroot(path=gencloud.config.GENTOO_MOUNT, shell="/bin/bash"):
    bind(mount=path)
    os.chroot(path)
    os.chdir(os.sep)
    os.system(shell)
    unbind(mount=path)

