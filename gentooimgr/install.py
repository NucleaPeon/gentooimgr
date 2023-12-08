"""Configure a Gentoo guest with cloud image settings

This step keeps track of how far it's gotten, so re-running this command
will continue on if an error was to occur, unless --start-over flag is given.
"""

import os
import sys
import shutil
import configparser
from subprocess import Popen, PIPE
import gentooimgr.config
import gentooimgr.configs
import gentooimgr.common
import gentooimgr.chroot
import gentooimgr.kernel
from gentooimgr import HERE

from gentooimgr.configs import *

FILES_DIR = os.path.join(HERE, "..")

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
        proc = Popen(c, stdout=PIPE, stderr=PIPE)
        stdout, stderr = proc.communicate()

    completestep(1, "diskprep")

def step2_mount(args, cfg):
    print(f'\t:: Step 2: Mounting {gentooimgr.config.GENTOO_MOUNT}')
    proc = Popen(["mount", f'{cfg.get("disk")}{cfg.get("partition")}', cfg.get("mountpoint")])
    proc.communicate()
    completestep(2, "mount")

def step3_stage3(args, cfg):
    print(f'\t:: Step 3: Stage3 Tarball')

    stage3 = cfg.get("stage3") or args.stage3  # FIXME: auto detect stage3 images in mountpoint and add here
    if not stage3:
        stage3 = gentooimgr.common.stage3_from_dir(FILES_DIR)


    proc = Popen(["tar", "xpf", os.path.abspath(stage3), "--xattrs-include='*.*'", "--numeric-owner", "-C",
                  f'{cfg.get("mountpoint")}'])
    proc.communicate()
    completestep(3, "stage3")

def step4_binds(args, cfg):
    print(f'\t:: Step 4: Binding Filesystems')
    gentooimgr.chroot.bind(verbose=False)
    completestep(4, "binds")

def step5_portage(args, cfg):
    print(f'\t:: Step 5: Portage')
    portage = cfg.get("portage") or args.portage
    if not portage:
        portage = gentooimgr.common.portage_from_dir(FILES_DIR)
    proc = Popen(["tar", "xpf", portage, "-C", f"{cfg.get('mountpoint')}/usr/"])
    proc.communicate()
    completestep(5, "portage")

def step6_licenses(args, cfg):
    print(f'\t:: Step 6: Licenses')
    license_path = os.path.join(cfg.get("mountpoint"), 'etc', 'portage', 'package.license')
    os.makedirs(license_path, exist_ok=True)
    for f, licenses in cfg.get("licensefiles", {}).items():
        with open(os.path.join(license_path, f), 'w') as f:
            f.write('\n'.join(licenses))
    completestep(6, "license")

def step7_repos(args, cfg):
    print(f'\t:: Step 7: Emerge Sync Repo')
    repo_path = os.path.join(cfg.get("mountpoint"), 'etc', 'portage', 'repos.conf')
    os.makedirs(repo_path)
    # Copy from template
    repo_file = os.path.join(repo_path, 'gentoo.conf')
    shutil.copyfile(
        os.path.join(cfg.get("mountpoint"), 'usr', 'share', 'portage', 'config', 'repos.conf'),
        repo_file)
    # Regex replace lines
    cp = configparser.ConfigParser()
    for repofile, data in cfg.get("repos", {}).items():
        cp.read(repofile)
        for section, d in data.items():
            for key, val in d.items():
                # Replace everything after the key with contents of value.
                # Sed is simpler than using regex for this purpose.
                cp.set(section, key, val)

    completestep(7, "repos")

def step8_resolv(args, cfg):
    print(f'\t:: Step 8: Resolv')
    proc = Popen(["cp", "--dereference", "/etc/resolv.conf", os.path.join(cfg.get("mountpoint"), 'etc')])
    proc.communicate()
    # Copy all step files and python module to new chroot
    os.system(f"cp /tmp/*.step {cfg.get('mountpoint')}/tmp")
    os.system(f"cp -r . {cfg.get('mountpoint')}/mnt/")
    completestep(8, "resolv")

def step9_sync(args, cfg):
    print(f"\t:: Step 9: sync")
    print("\t\t:: Entering chroot")
    os.chroot(cfg.get("mountpoint"))
    os.chdir(os.sep)
    proc = Popen(["emerge", "--sync", "--quiet"])
    proc.communicate()
    completestep(9, "sync")

def step10_emerge_pkgs(args, cfg):
    print(f"\t:: Step 10: emerge pkgs")
    packages = cfg.get("packages", {})
    for oneshot_up in packages.get("oneshots", []):
        proc = Popen(["emerge", "--oneshot", "--update", oneshot_up])
        proc.communicate()

    for single in packages.get("singles", []):
        proc = Popen(["emerge", single])
        proc.communicate()

    for keepgoing in packages.get("keepgoing", []):
        proc = Popen(["emerge", keepgoing])
        proc.communicate()

    cmd = ["emerge", "-j", str(args.threads), "--keep-going"]
    proc = Popen(cmd)
    proc.communicate()

    cmd = ["emerge", "-j", str(args.threads)]
    cmd.extend(packages.get("kernel", []))
    cmd.extend(packages.get("base", []))
    cmd.extend(packages.get("additional", []))
    cmd.extend(packages.get("bootloader", []))
    proc = Popen(cmd)
    proc.communicate()
    completestep(10, "pkgs")

def step11_kernel(args, cfg):
    # at this point, genkernel will be installed
    print(f"\t:: Step 11: kernel")
    proc = Popen(["eselect", "kernel", "set", "1"])
    proc.communicate()
    if not args.kernel_dist:
        os.chdir(os.path.join(os.sep, 'usr', 'src', 'linux'))
        threads = str(gentooimgr.config.THREADS)
        for cmd in [
            ["make", "defconfig", "-j", threads],
            ["make", "kvm_guest", "-j", threads],  # This should be toggled with --virtio option (--config-kvm?)
            ["genkernel", "all"]]:
            proc = Popen(cmd)
            proc.communicate()

    completestep(11, "kernel")

def step12_grub(args, cfg):
    print(f"\t:: Step 12: kernel")
    proc = Popen(["grub-install", gentooimgr.config.CLOUD_CFG['disk']])
    proc.communicate()
    code = proc.returncode
    if code != 0:
        sys.stderr.write(f"Failed to install grub on {gentooimgr.config.CLOUD_CFG['disk']}\n")
        sys.exit(code)

    with open("/etc/default/grub", 'w') as f:
        f.write(f"{gentooimgr.kernel.GRUB_CFG}")

    proc = Popen(["grub-mkconfig", "-o", "/boot/grub/grub.cfg"])
    proc.communicate()
    completestep(12, "grub")

def step13_serial(args, cfg):
    print(f"\t:: Step 13: Serial")
    os.system("sed -i 's/^#s0:/s0:/g' /etc/inittab")
    os.system("sed -i 's/^#s1:/s1:/g' /etc/inittab")
    completestep(13, "serial")

def step14_services(args, cfg):
    print(f"\t:: Step 14: Services")
    for service in ["acpid", "syslog-ng", "cronie", "sshd", "cloud-init-local", "cloud-init", "cloud-config",
                    "cloud-final", "ntpd", "nfsclient"]:
        if args.profile == "systemd":
            proc = Popen(["systemctl", "enable", service])
        else:
            proc = Popen(["rc-update", "add", service, "default"])
        proc.communicate()

    completestep(14, "services")

def step15_ethnaming(args, cfg):
    print(f"\t:: Step 15: Eth Naming")
    completestep(15, "networking")

def step16_sysconfig(args, cfg):
    print(f"\t:: Step 16: Sysconfig")
    with open("/etc/timezone", "w") as f:
        f.write("UTC")
    proc = Popen(["emerge", "--config", "sys-libs/timezone-data"])
    proc.communicate()
    with open("/etc/locale.gen", "a") as f:
        f.write("en_US.UTF-8 UTF-8\nen_US ISO-8859-1\n")
    proc = Popen(["locale-gen"])
    proc.communicate()
    proc = Popen(["eselect", "locale", "set", "en_US.utf8"])
    proc.communicate()
    proc = Popen(["env-update"])
    proc.communicate()
    with open('/etc/sysctl.d/swappiness.conf', 'w') as f:
        f.write("vm.swappiness = 0\n")

    modloadpath = os.path.join(os.sep, 'etc', 'modules-load.d')
    os.makedirs(modloadpath)
    with open(os.path.join(modloadpath, 'cloud-modules.conf'), 'w') as f:
        f.write('\n'.join(gentooimgr.configs.CLOUD_MODULES))

    cloudcfg = os.path.join(os.sep, 'etc', 'cloud')
    if not os.path.exists(cloudcfg):
        os.makedirs(cloudcfg)
        os.makedirs(os.path.join(cloudcfg, 'templates'))
    with open(os.path.join(cloudcfg, 'cloud.cfg'), 'w') as cfg:
        cfg.write(f"{CLOUD_YAML}")

    os.chmod(os.path.join(cloudcfg, "cloud.cfg"), 0o644)

    with open(os.path.join(cloudcfg, "templates", "hosts.gentoo.tmpl"), 'w') as tmpl:
        tmpl.write(f"{HOST_TMPL}") # FIXME:

    os.chmod(os.path.join(cloudcfg, "templates", "hosts.gentoo.tmpl"), 0o644)

    proc = Popen("sed -i 's/domain_name\,\ domain_search\,\ host_name/domain_search/g' /etc/dhcpcd.conf", shell=True)
    proc.communicate()

    hostname = os.path.join(os.sep, 'etc', 'conf.d', 'hostname')
    with open(hostname, 'w') as f:
        f.write(f"{HOSTNAME}\n")

    os.chmod(hostname, 0o644)

    proc = Popen(["eix-update"])
    proc.communicate()

    os.remove(os.path.join(os.sep, 'etc', 'resolv.conf'))

    completestep(16, "sysconfig")

def step17_fstab(args, cfg):
    print(f"\t:: Step 17: fstab")
    with open(os.path.join(os.sep, 'etc', 'fstab'), 'a') as fstab:
        fstab.write(f"{gentooimgr.config.CLOUD_CFG.get('disk')}\t/\text4\tdefaults,noatime\t0 1\n")

    completestep(17, "fstab")

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

def configure(args, config: dict):
    # Load configuration
    if not os.path.exists(gentooimgr.config.GENTOO_MOUNT):
        if not args.force:
            # We aren't in a gentoo live cd are we?
            sys.stderr.write("Your system doesn't look like a gentoo live cd, exiting for safety.\n"
                "If you want to continue, use --force option and re-run `python -m gentooimgr install` with your configuration\n")
            sys.exit(1)

        else:
            # Assume we are root as per live cd, otherwise user should run this as root as a secondary confirmation
            os.makedirs(gentooimgr.config.GENTOO_MOUNT)
    # disk prep
    cfg = config
    if not stepdone(1): step1_diskprep(args, cfg)
    # mount root
    if not stepdone(2): step2_mount(args, cfg)
    # extract stage
    if not stepdone(3): step3_stage3(args, cfg)
    # mount binds
    if not stepdone(4): step4_binds(args, cfg)
    # extract portage
    if not stepdone(5): step5_portage(args, cfg)
    # Set licenses
    if not stepdone(6): step6_licenses(args, cfg)
    # repos.conf
    if not stepdone(7): step7_repos(args, cfg)
    # portage env files and resolv.conf
    if not stepdone(8): step8_resolv(args, cfg)
    # emerge --sync
    if not stepdone(9): step9_sync(args, cfg)
    # bindist
    if not stepdone(10): step10_emerge_pkgs(args, cfg)
    # emerge packages
    # configure & emerge kernel (use cloud configuration too)
    if not stepdone(11): step11_kernel(args, cfg)
    # grub
    if not stepdone(12): step12_grub(args, cfg)
    # enable serial console
    if not stepdone(13): step13_serial(args, cfg)
    # services
    if not stepdone(14): step14_services(args, cfg)
    # eth0 naming
    # timezone
    if not stepdone(15): step15_ethnaming(args, cfg)
    # locale
    # set some sysctl things
    # set some dhcp things
    # hostname
    if not stepdone(16): step16_sysconfig(args, cfg)
    # fstab
    if not stepdone(17): step17_fstab(args, cfg)
    # copy cloud cfg?
    gentooimgr.chroot.unbind()
    # Finish install processes like emaint and eix-update and news read


