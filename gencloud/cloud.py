"""Configure a Gentoo guest with cloud image settings

This step keeps track of how far it's gotten, so re-running this command
will continue on if an error was to occur, unless --start-over flag is given.
"""

import os
import sys
from subprocess import Popen, PIPE
import gencloud.config
import gencloud.common

def step1_diskprep(args, cfg):
    # http://rainbow.chard.org/2013/01/30/how-to-align-partitions-for-best-performance-using-parted/
    # http://honglus.blogspot.com/2013/06/script-to-automatically-partition-new.html
    cmds = [
            ['parted', '-s', f'{cfg.get("disk")}', 'mklabel', 'msdos'],
            ['parted', '-s', f'{cfg.get("disk")}', 'mkpart', 'primary', '2048s', '100%'],
            ['partprobe'],
            ['mkfs.ext4', '-FF', f'{cfg.get("disk")}{cfg.get("partition", 1)}']
    ]
    for c in cmds:
        print(f"\t:: {c}")
        proc = Popen(c, stdout=PIPE, stderr=PIPE)
        proc.communicate()

    completestep(1, "diskprep")

def step2_mount(args, cfg):
    proc = Popen(["mount", f'{cfg.get("disk")}{cfg.get("partition")}', gencloud.config.GENTOO_MOUNT])
    proc.communicate()
    completestep(2, "mount")

def completestep(step, stepname, prefix='/tmp'):
    with open(os.path.join(prefix, f"{step}.step"), 'w') as f:
        f.write("done.")  # text in this file is not currently used.

def getlaststep(prefix='/tmp'):
    i = 1
    found = False
    while not found:
        if os.path.exists(f"{i}.step"):
            i += 1
        else:
            found = True

    return i


def stepdone(step, prefix='/tmp'):
    return os.path.exists(os.path.join(prefix, f"{step}.step"))

def configure(args):
    # Load configuration
    if not os.path.exists(gencloud.config.GENTOO_MOUNT):
        if not args.force:
            # We aren't in a gentoo live cd are we?
            sys.stderr.write("Your system doesn't look like a gentoo live cd, exiting for safety.\n"
                "If you want to continue, use --force option and re-run `python -m gencloud cloud-cfg`\n")
            sys.exit(1)

        else:
            # Assume we are root as per live cd, otherwise user should run this as root as a secondary confirmation
            os.makedirs(gencloud.config.GENTOO_MOUNT)
    # disk prep
    cfg = gencloud.common.load_config(args)
    print(f"\t:: Configuration {cfg}")
    if not stepdone(1): step1_diskprep(args, cfg)
    if not stepdone(2): step2_mount(args, cfg)
    # mount root
    # extract stage
    # mount binds
    # extract portage
    # Set licenses
    # repos.conf
    # portage env files and resolv.conf
    # emerge --sync
    # bindist
    # emerge packages
    # configure & emerge kernel (use cloud configuration too)
    # grub
    # enable serial console
    # services
    # eth0 naming
    # timezone
    # locale
    # set some sysctl things
    # set some dhcp things
    # hostname
    # fstab
    # copy cloud cfg?
    # Finish install processes like emaint and eix-update and news read
