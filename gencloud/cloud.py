"""Configure a Gentoo guest with cloud image settings

This step keeps track of how far it's gotten, so re-running this command
will continue on if an error was to occur, unless --start-over flag is given.
"""

import os
import sys
import shutil
from subprocess import Popen, PIPE
import gencloud.config
import gencloud.common
import gencloud.chroot

def step1_diskprep(args, cfg):
    print("\t:: Step 1: Disk Partitioning")
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
    print(f'\t:: Step 2: Mounting {gencloud.config.GENTOO_MOUNT}')
    proc = Popen(["mount", f'{cfg.get("disk")}{cfg.get("partition")}', gencloud.config.GENTOO_MOUNT])
    proc.communicate()
    completestep(2, "mount")

def step3_stage3(args, cfg):
    print(f'\t:: Step 3: Stage3 Tarball')
    proc = Popen(["tar", "xpf", cfg.get("stage3"), "--xattrs-include='*.*'", "--numeric-owner" "-C",
                  f'{gencloud.config.GENTOO_MOUNT}'])
    proc.communicate()
    completestep(3, "stage3")

def step4_binds(args, cfg):
    print(f'\t:: Step 4: Binding Filesystems')
    gencloud.chroot.bind(verbose=False)
    completestep(4, "binds")

def step5_portage(args, cfg):
    print(f'\t:: Step 5: Portage')
    proc = Popen(["tar", "-xjpf", cfg.get("portage"), "-C", f"{gencloud.config.GENTOO_MOUNT}/usr/"])
    proc.communicate()
    completestep(5, "portage")

def step6_licenses(args, cfg):
    print(f'\t:: Step 6: Licenses')
    license_path = os.path.join(gencloud.config.GENTOO_MOUNT, 'etc', 'portage', 'package.license')
    os.makedirs(license_path)
    for f, licenses in gencloud.config.GENTOO_ACCEPT_LICENSES.items():
        with open(f, 'w') as f:
            f.write('\n'.join(licenses))
    completestep(6, "license")

def step7_repos(args, cfg):
    print(f'\t:: Step 7: Emerge Sync Repo')
    repo_path = os.path.join(gencloud.config.GENTOO_MOUNT, 'etc', 'portage', 'repos.conf')
    os.makedirs(repo_path)
    with open(os.path.join(repo_path, 'gentoo.conf'), 'w') as f:
        f.write(gencloud.config.GENTOO_REPO_FILE)

    completestep(7, "repos")

def step8_resolv(args, cfg):
    print(f'\t:: Step 8: Resolv')
    proc = Popen(["cp", "--dereference", "/etc/resolv.conf", os.path.join(gencloud.config.GENTOO_MOUNT, 'etc'])])
    proc.communicate()
    completestep(8, "resolv")

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
    if not stepdone(1): step1_diskprep(args, cfg)
    # mount root
    if not stepdone(2): step2_mount(args, cfg)
    # extract stage
    if not stepdone(3): step3_stage3(args, cfg)
    # mount binds
    if not stepdone(4): step4_binds(args, cfg)
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
