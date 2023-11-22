import sys
import gentooimgr.chroot

def command(*args):
    gentooimgr.chroot.bind()
    for a in args:
        proc = Popen(a, shell=True, stdout=PIPE, stderr=PIPE)
        stdout, stderr = proc.communicate()
        if proc.returncode != 0:
            sys.stderr.write(f"{stderr}\n")
            break
    gentooimgr.chroot.unbind()
