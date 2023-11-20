import sys
import gencloud.chroot

def command(*args):
    gencloud.chroot.bind()
    for a in args:
        proc = Popen(a, shell=True, stdout=PIPE, stderr=PIPE)
        stdout, stderr = proc.communicate()
        if proc.returncode != 0:
            sys.stderr.write(f"{stderr}\n")
            break
    gencloud.chroot.unbind()
