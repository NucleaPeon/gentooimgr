import sys
import gentooimgr.chroot
import gentooimgr.errorcodes
from gentooimgr.logging import LOG

def command(config, *args) -> int:
    code = gentooimgr.chroot.bind()
    for a in args:
        proc = Popen(a, shell=True, stdout=PIPE, stderr=PIPE)
        stdout, stderr = proc.communicate()
        if proc.returncode != 0:
            LOG.error(f"{stderr}\n")
            code = gentooimgr.errorcodes.PROCESS_FAILED

    if code == gentooimgr.errorcodes.SUCCESS:
        code = gentooimgr.chroot.unbind()
    else:
        gentooimgr.chroot.unbind()
    return code
