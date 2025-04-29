"""
Allows user to run steps by specifying the number
"""

from gentooimgr.install import STEPS, STEP_FUNCS

def list_steps():
    """
    :Parameters:
        - steps: a list of positive integers or 0, which will print out a list of steps and their short descriptions
    """
    for k, v in STEPS.items():
        print(f"Step {k}: {v}")


def run_step(args, cfg, *steps):
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
            print(f"Step in {s} was not a valid integer")


    print(f"Running steps {run_these}")

    if 0 in steps:
        return list_steps()

    for runstep in run_these:
        STEP_FUNCS.get(runstep, print)(args, cfg)


