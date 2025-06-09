from subprocess import Popen, PIPE
from gentooimgr.logging import LOG
from time import sleep

import os
import fcntl

def run(cmd, stdout=PIPE, stderr=PIPE, stdin=PIPE, env=None):
    """Run commands without args, standalone
    """
    if env is not None:
        LOG.debug("Running command with a custom environment")
    proc = Popen(cmd, stdout=stdout, stderr=stderr, stdin=stdin, env=env)
    out, err = proc.communicate()
    if out:
        LOG.debug(f"run cmd output {out}")
    if err:
        # Force logging of errors if found
        LOG.error(str(err))
    return (proc.returncode, out, err,)

def run_cmd(args, cmd=[], stdout=None, stderr=None, stdin=None, env=None):
    if args.pretend:
        LOG.info(f"PRETEND {' '.join(cmd)}")
        return (0, "", "",)

    try:
        LOG.debug(f'Run cmd {" ".join(cmd)}')
    except:
        pass
    return run(cmd, stdout=stdout, stderr=stderr, stdin=stdin, env=env)

def setNonBlocking(fd):
    """
    Set the file description of the given file descriptor to non-blocking.
    """
    flags = fcntl.fcntl(fd, fcntl.F_GETFL)
    flags = flags | os.O_NONBLOCK
    fcntl.fcntl(fd, fcntl.F_SETFL, flags)
#
# def start(executable_file):
#     p = Popen(
#         executable_file,
#         stdin=PIPE,
#         stdout=PIPE,
#         stderr=PIPE)
#     setNonBlocking(p.stdout)
#     setNonBlocking(p.stderr)
#     return p
#
# def read(process):
#     while True:
#         try:
#             out1 = process.stdout.readline().decode("utf-8").strip()
#         except IOError:
#             continue
#         else:
#             break
#     out1 = process.stdout.readline().decode("utf-8").strip()
#     return out1
#
# def write(process, message):
#     process.stdin.write(f"{message.strip()}\n".encode("utf-8"))
#     process.stdin.flush()
#
#
#
# def terminate(process):
#     process.stdin.close()
#     process.terminate()
#     process.wait(timeout=0.2)
#
#
# def run_interactive(cmd, *additional):
#     import pexpect
#
#     child = pexpect.spawn("mac-fdisk /dev/sda")
#     child.expect("/dev/sda")
#     child.sendline("i")
#     part_exists = "map already exists"
#     part_empty = "size of 'device' is"
#     child.expect([part_exists, part_empty])
#     if part_exists.encode() in child.after:
#         child.sendline("y")
#
#     child.sendline("\n")
#     child.expect("new size of 'device' is")
#     child.sendline("b")
    # proc = Popen(["mac-fdisk", "/dev/sda"], stdin=PIPE, stdout=PIPE, stderr=PIPE)
    # setNonBlocking(p.stdout)
    # setNonBlocking(p.stderr)
    # proc.communicate(b'')
    # proc.stdin.write(b"p\n") #send "connect"
    # sleep(0.1)
    # while True:
    #     output = p.stdout.read() # <-- Hangs here!
    #     if not output:
    #         print '[No more data]'
    #         break
    #
    # print(proc.stdout.readline(), flush=True)
    # print(proc.stderr.read())
    # # print(proc.stderr.readline(), flush=True)
    # proc.stdin.write(b"q\n")
    # # proc.stdin.write(b"exit\n") #send "exit"
    # # print(proc.stdout.readline(), flush=True)
    # proc.stdin.close() #close stdin (like hitting Ctrl+D in the terminal)
    # proc.wait() #wait until process terminates
    # proc = Popen(["mac-fdisk", "/dev/sda"], stdin=PIPE, stdout=PIPE)
    # o, e = proc.communicate()
    # print(o, e)
    # proc.stdin.write(b"i\n") # initialize partition map
    # # o, e = proc.communicate()
    # print(o, e)
    # if "do you want to reinit?" in o:
    #     proc.stdin.write(b"y\n")
    #
    # o, e = proc.communicate()
    # print(o, e)
    # proc.stdin.write(b"q\n") #send "exit"
    # time.sleep(0.1)
    # proc.stdin.close() #close stdin (like hitting Ctrl+D in the terminal)
    # proc.wait() #wait until process terminates

