"""
Allows user to run steps by specifying the number
"""
import sys

import gentooimgr.chroot
from gentooimgr.install import STEPS, STEP_FUNCS

def list_steps():
    """
    :Parameters:
        - steps: a list of positive integers or 0, which will print out a list of steps and their short descriptions
    """
    for k, v in STEPS.items():
        print(f"Step {k}: {v}")


def run_step(args, cfg, *steps):
    """Warning: Steps do not factor in the need for chroot, you may
    be in the chroot and not want to have the chroot function called, whereas you might also specify a single step and need the chroot done and undone before/after the step.

    For this reason, specifying a single step that is in the 9+ range will always perform the chroot function.
    """
    run_these = []
    for s in steps:
        try:
            if isinstance(s, str) and '-' in s:
                # this is a range
                split = s.split("-")
                int(split[0])
                int(split[1])
                run_these += range(split[0], split[1])
                continue

            int(s)
            assert s >= 0
            run_these.append(s)
        except:
            sys.stderr.write(f"Step in {s} was not a valid integer\n")
            sys.exit(1)


    if 0 in steps:
        return list_steps()

    if len(run_these) == 1 and run_these[0] >= 9:
        STEP_FUNCS.get('chroot', print)(args, cfg)

    for runstep in run_these:
        STEP_FUNCS.get(runstep, print)(args, cfg)

    if len(run_these) == 1 and run_these[0] >= 9:
        gentooimgr.chroot.unbind()
