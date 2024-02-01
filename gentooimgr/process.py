from subprocess import Popen, PIPE
from gentooimgr.logging import LOG

def run_cmd(args, cmd=[], stdout=None, stderr=None, stdin=None, env=None):
    if args.pretend:
        LOG.info(f"PRETEND {' '.join(cmd)}")
        return (0, "", "",)

    try:
        LOG.debug(f'Run cmd {" ".join(cmd)}')
    except:
        pass
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
