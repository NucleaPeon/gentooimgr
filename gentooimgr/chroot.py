import os
import sys
from subprocess import Popen, PIPE
import gentooimgr.config
from gentooimgr.logging import LOG
import gentooimgr.errorcodes

def bind(mount=gentooimgr.config.GENTOO_MOUNT, verbose=True):
    mounts = [
        ["mount", "--types", "proc", "/proc", os.path.join(mount, "proc")],
        ["mount", "--rbind", "/sys", os.path.join(mount, "sys")],
        ["mount", "--make-rslave", os.path.join(mount, "sys")],
        ["mount", "--rbind", "/dev", os.path.join(mount, "dev")],
        ["mount", "--make-rslave", os.path.join(mount, "dev")],
        ["mount", "--bind", "/run", os.path.join(mount, "run")],
        ["mount", "--make-slave", os.path.join(mount, "run")],
    ]
    code = gentooimgr.errorcodes.SUCCESS
    for mcmd in mounts:
        if verbose:
            LOG.debug(f"\t:: {' '.join(mcmd)}")
        proc = Popen(mcmd, stdout=PIPE, stderr=PIPE)
        stdout, stderr = proc.communicate()
        if proc.returncode != 0:
            LOG.error(f"stderr: {stderr}\nstdout: {stdout}")
            code = gentooimgr.errorcodes.PROCESS_FAILED

    return proc.returncode


def unbind(mount=gentooimgr.config.GENTOO_MOUNT, verbose=True):
    """It's worth noting that if you unmount (unbind) right after you exit the shell
    in an automated process, there will be errors produced. If you run
    ```
    python -m gentooimgr unchroot
    ```
    from an interactive prompt and it still gives errors, then that could constitute
    a problem. At this point in the process, if there are lingering mounts, a reboot
    may solve them regardless.
    """
    os.chdir("/")
    if not os.path.exists(mount):
        LOG.error(f"Mountpoint {mount} does not exist\n")
        return

    unmounts = [
        ["umount", os.path.join(mount, 'dev', 'shm')],
        ["umount", os.path.join(mount, 'dev', 'pts')],
        ["umount", "-l", os.path.join(mount, 'dev')],
        ["umount", "-R", mount]
    ]
    code = gentooimgr.errorcodes.SUCCESS
    for uncmd in unmounts:
        if verbose:
            LOG.debug(f"\t:: {' '.join(uncmd)}")
        proc = Popen(uncmd, stdout=PIPE, stderr=PIPE)
        stdout, stderr = proc.communicate()
        if proc.returncode != 0:
            if stderr or stdout:
                LOG.error(f"{uncmd}\n\tstderr: {stderr}\n\tstdout: {stdout}")
                code = gentooimgr.errorcodes.PROCESS_FAILED

    return code


def chroot(path=gentooimgr.config.GENTOO_MOUNT, shell="/bin/bash") -> int:
    code = bind(mount=path)
    if code == gentooimgr.errorcodes.SUCCESS:
        os.chroot(path)
        os.chdir(os.sep)
        os.system(shell)
        code = unchroot(path=path)  # May fail if we do this automatically
    return code


def unchroot(path=gentooimgr.config.GENTOO_MOUNT) -> int:
    return unbind(mount=path)
