"""Configure a Gentoo guest with cloud image settings

This step keeps track of how far it's gotten, so re-running this command
will continue on if an error was to occur, unless --start-over flag is given.
"""

import os
import sys
import shutil
import configparser
from subprocess import PIPE
import gentooimgr.config
import gentooimgr.configs
import gentooimgr.common
import gentooimgr.chroot
import gentooimgr.kernel
import gentooimgr.errorcodes
from gentooimgr.process import run_cmd
from gentooimgr import HERE
from gentooimgr.logging import LOG

from gentooimgr.configs import *

FILES_DIR = os.path.join(HERE, "..")
LAST_STEP = 18

def step1_diskprep(args, cfg):
    LOG.info(":: Step 1: Disk Preparation")
    # http://rainbow.chard.org/2013/01/30/how-to-align-partitions-for-best-performance-using-parted/
    # http://honglus.blogspot.com/2013/06/script-to-automatically-partition-new.html
    cmds = []
    partnum = 1
    if args.parttype == "efi":
        cmds.extend([
            ['parted', '-s', f'{cfg.get("disk")}', 'mklabel', "GPT"],
            ['parted', '-s', f'{cfg.get("disk")}', 'mkpart', 'primary', 'fat32', '1MiB', '321MiB'],
            ['parted', '-s', f'{cfg.get("disk")}', 'set', str(partnum), 'boot', 'on'],
            ['parted', '-s', f'{cfg.get("disk")}', 'set', str(partnum), 'esp', 'on']
        ])
        partnum += 1

    else:
        cmds.append(['parted', '-s', f'{cfg.get("disk")}', 'mklabel', "msdos"])

    cmds.extend([
        ['parted', '-s', f'{cfg.get("disk")}', 'mkpart', 'primary', '321MiB', '100%'], # is 2048s correct?
        ['partprobe'],
        ['mkfs.ext4', '-FF', f'{cfg.get("disk")}{partnum}']
    ])
    partnum += 1  # in case we use this later, reflect partition number to use next.
    if args.parttype == "efi":
        cmds.append(['mkfs.vfat', '-F32', '-n', 'EFI', f'{cfg.get("disk")}1'])

    for c in cmds:
        run_cmd(args, c, stdout=PIPE, stderr=PIPE)

    completestep(args, 1, "diskprep")

def step2_mount(args, cfg):
    LOG.info(f":: Step 2: Mounting {gentooimgr.config.GENTOO_MOUNT}")

    partnum = 1
    cmd = []
    if args.parttype == "efi":
        cmd.extend([
            ["mount", f'{cfg.get("disk")}{partnum+1}', f"{cfg.get('mountpoint')}"],
            ["mkdir", "-p", f"{cfg.get('mountpoint')}/boot/efi"],
            ["mount", f'{cfg.get("disk")}{partnum}', f"{cfg.get('mountpoint')}/boot/efi"],
            ["mkdir", "-p", f"{cfg.get('mountpoint')}/boot/efi/EFI/BOOT/"]
        ])
    else:
        cmd.append(["mount", f'{cfg.get("disk")}{partnum}', f"{cfg.get('mountpoint')}"])

    for c in cmd:
        run_cmd(args, c, stdout=PIPE, stderr=PIPE)
    completestep(args, 2, "mount")

def step3_stage3(args, cfg):
    LOG.info(f":: Step 3: Stage3 Tarball")
    stage3 = cfg.get("stage3") or args.stage3  # FIXME: auto detect stage3 images in mountpoint and add here
    if not stage3:
        stage3 = gentooimgr.common.stage3_from_dir(FILES_DIR)

    LOG.info(f"\t:: Stage 3 file selected: {stage3}")
    cmd = ["tar", "xpf", os.path.abspath(stage3), "--xattrs-include='*.*'", "--numeric-owner", "-C",
                  f'{cfg.get("mountpoint")}']
    run_cmd(args, cmd)
    completestep(args, 3, "stage3")

def step4_binds(args, cfg):
    LOG.info(':: Step 4: Binding Filesystems')
    if not args.pretend: gentooimgr.chroot.bind(verbose=args.debug)
    completestep(args, 4, "binds")

def step5_portage(args, cfg):
    LOG.info(':: Step 5: Portage')
    portage = cfg.get("portage") or args.portage
    if not portage:
        portage = gentooimgr.common.portage_from_dir(FILES_DIR)

    portage = str(portage)  # --portage = posixpath, not str
    LOG.info(f"\t:: Portage file selected: {portage}")
    run_cmd(args, ["tar", "xpf", portage, "-C", f"{cfg.get('mountpoint')}/usr/"])
    # Edit portage
    portage_env = os.path.join(cfg.get("mountpoint"), 'etc', 'portage', 'env')
    os.makedirs(portage_env, exist_ok=True)
    with open(os.path.join(portage_env, 'singlejob.conf'), 'w') as f:
        f.write('MAKEOPTS="-j1"\n')
    LOG.info("\t:: Portage single job configuration file written")

    env_path = os.path.join(cfg.get("mountpoint"), 'etc', 'portage', 'package.env')
    with open(env_path, 'w') as f:
        f.write("app-portage/eix singlejob.conf\ndev-util/maturin singlejob.conf\ndev-util/cmake singlejob.conf")
    LOG.info("\t:: Portage package environment configuration file written")

    completestep(args, 5, "portage")

def step6_licenses(args, cfg):
    LOG.info(':: Step 6: Licenses')
    license_path = os.path.join(cfg.get("mountpoint"), 'etc', 'portage', 'package.license')
    os.makedirs(license_path, exist_ok=True)
    for f, licenses in cfg.get("licensefiles", {}).items():
        LOG.info(f"\t:: Writing {f} license file")
        with open(os.path.join(license_path, f), 'w') as f:
            f.write('\n'.join(licenses))
    completestep(args, 6, "license")

def step7_repos(args, cfg):
    LOG.info(':: Step 7: Repo Configuration')
    repo_path = os.path.join(cfg.get("mountpoint"), 'etc', 'portage', 'repos.conf')
    if not args.pretend: os.makedirs(repo_path, exist_ok=True)
    # Copy from template
    repo_file = os.path.join(repo_path, 'gentoo.conf')
    if not args.pretend: shutil.copyfile(
        os.path.join(cfg.get("mountpoint"), 'usr', 'share', 'portage', 'config', 'repos.conf'),
        repo_file)
    LOG.info(f"\t:: Repo configuration file copied {repo_file}")
    # Regex replace lines
    if not args.pretend:
        cp = configparser.ConfigParser()
        for repofile, data in cfg.get("repos", {}).items():
            cp.read(cfg.get("mountpoint") + repofile)  # repofile should be absolute path, do not use os.path.join.
            for section, d in data.items():
                if section in cp:
                    for key, val in d.items():
                        # Replace everything after the key with contents of value.
                        # Sed is simpler than using regex for this purpose.
                        cp.set(section, key, val)
                else:
                    LOG.warning(f"\tWW No section {section} in {repofile}\n")

            cp.write(open(cfg.get("mountpoint") + repofile, 'w'))

    completestep(args, 7, "repos")

def step8_resolv(args, cfg):
    LOG.info(f':: Step 8: Resolv')
    if not os.path.exists(cfg.get("mountpoint")):
        return
    run_cmd(args, ["cp", "--dereference", "/etc/resolv.conf", os.path.join(cfg.get("mountpoint"), 'etc')])
    # Copy all step files and python module to new chroot
    if not args.pretend:
        os.system(f"cp /tmp/*.step {cfg.get('mountpoint')}/tmp")
        os.system(f"cp -r . {cfg.get('mountpoint')}/mnt/")
    completestep(args, 8, "resolv")

def step9_sync(args, cfg):
    LOG.info(f":: Step 9: sync")
    os.chdir(os.sep)
    env = os.environ
    if args.ignore_collisions:
        os.environ['COLLISION_IGNORE'] = f"{' '.join(args.ignore_collisions)}"
    os.system("source /etc/profile")
    run_cmd(args, ["emerge", "--sync", "--quiet"])
    LOG.debug("\t:: Sync'd")
    LOG.info("\t:: Emerging base")
    run_cmd(args, ["emerge", "--update", "--deep", "--newuse", "--keep-going", "@world"], env=env)
    LOG.debug("\t:: World Emerged")
    completestep(args, 9, "sync")

def step10_emerge_pkgs(args, cfg):
    LOG.info(f":: Step 10: emerge pkgs")
    packages = cfg.get("packages", {})
    env = os.environ
    if args.ignore_collisions:
        os.environ['COLLISION_IGNORE'] = ' '.join(args.ignore_collisions)
    for one in packages.get("oneshots", []):
        LOG.debug(f"\t:: Oneshot packages: {one}")
        run_cmd(args, ["emerge", "--oneshot", one])

    for single in packages.get("singles", []):
        LOG.debug(f"\t:: Single packages: {single}")
        run_cmd(args, ["emerge", "-j", "1", single], env=env)

    if packages.get("kernel", []):
        run_cmd(args, ["emerge", "-j", str(args.threads)] + packages.get("kernel", []), env=env)

    cmd = ["emerge", "-j", str(args.threads), "--keep-going"]
    cmd += packages.get("keepgoing", [])
    run_cmd(args, cmd, env=env)
    if args.parttype == "efi" and not args.pretend:
        LOG.info(":: Setting GRUB_PLATFORMS in make.conf")
        with open('/etc/portage/make.conf', 'a') as make_conf:
            make_conf.write("GRUB_PLATFORMS=\"efi-64\"\n")

    cmd = ["emerge", "-j", str(args.threads)]
    cmd += packages.get("bootloader", ['sys-boot/grub:2'])
    run_cmd(args, cmd, env=env)
    LOG.info("\t:: Installing {}".format(packages.get("bootloader")))
    cmd = ["emerge", "-j", str(args.threads)]
    cmd += packages.get("base", [])
    cmd += packages.get("additional", [])
    cmd += args.packages or []
    run_cmd(args, cmd, env=env)
    try:
        run_cmd(args, ["eix-update"], env=env)
        LOG.debug("\t:: eix Updated")
    except Exception as E:
        # eix is assumed to be installed based on our base.json package, but custom configs may not have it.
        # That means this is non-essential to occur.
        LOG.warning("eix-update failed to run, is eix installed?")
    completestep(args, 10, "pkgs")

def step11_kernel(args, cfg):
    # at this point, genkernel will be installed. Please note that configuration files must be copied before this point
    LOG.info(f":: Step 11: kernel")
    run_cmd(args, ["eselect", "kernel", "set", "1"])
    if not args.kernel_dist and not args.pretend:
        gentooimgr.kernel.build_kernel(args, cfg, inchroot=not os.path.exists('/mnt/gentoo'))

    if args.parttype == "efi" and not args.pretend:
        # We need to copy the /boot/efi/{vmlinuz/System/initramfs files to /boot
        path = "/boot/efi"
        copyfiles = os.listdir(path)
        for f in copyfiles:
            if f.startswith("vmlinuz") or f.startswith("initramfs") or f.startswith("System"):
                if args.pretend:
                    LOG.info(f"copy {os.path.join(path, f)} {os.path.join(os.sep, 'boot', f)}")

                else:
                    shutil.copyfile(os.path.join(path, f), os.path.join(os.sep, 'boot', f))
                    LOG.debug(f"\t:: Copying {path}/{f} to /boot/{f}")

    completestep(args, 11, "kernel")

def step12_grub(args, cfg):
    LOG.info(f":: Step 12: kernel")
    cmd = ["grub-install"]
    if args.parttype == "efi":
        cmd += ["--target=x86_64-efi", '--efi-directory=/boot/efi']
    cmd.append(cfg.get('disk'))
    code, out, err = run_cmd(args, cmd, stderr=PIPE)
    code, out, err = run_cmd(args, ["eselect", "kernel", "set", "1"], stderr=PIPE, stdout=PIPE)
    if code != 0:
        sys.exit(code)

    grubcli = cfg.get("kernel", {}).get("commandline", "")
    if grubcli and not args.pretend:
        with open("/etc/default/grub", 'w') as f:
            grubtxt = gentooimgr.kernel.gen_grub_cfg(grubcli)
            f.write(f"{grubtxt}")

    run_cmd(args, ["grub-mkconfig", "-o", "/boot/grub/grub.cfg"])
    # if using efi, copy resulting grubx64.efi to bootx64.efi
    if args.parttype == "efi" and not args.pretend:
        shutil.copyfile("/boot/efi/EFI/gentoo/grubx64.efi", "/boot/efi/EFI/BOOT/bootx64.efi")
        # copy efi files to refind directory
        bootdir = "/boot"
        files = os.listdir(bootdir)
        to_copy = [f for f in files if f.startswith("vmlinuz") or f.startswith("initramfs")]
        for f in to_copy:
            shutil.copyfile(os.path.join(bootdir, f),
                            os.path.join(bootdir, "efi", 'EFI', 'gentoo', f))

    completestep(args, 12, "grub")

def step13_serial(args, cfg):
    LOG.info(f":: Step 13: Serial")
    if cfg.get("serial") and not args.pretend:
        os.system("sed -i 's/^#s0:/s0:/g' /etc/inittab")
        os.system("sed -i 's/^#s1:/s1:/g' /etc/inittab")
    completestep(args, 13, "serial")

def step14_networking(args, cfg):
    LOG.info(f":: Step 14: Services")
    os.chdir('/etc/init.d')
    os.symlink('net.lo', 'net.eth0')
    # link /etc/init.d/net.lo ->/etc/init.d/net.eth0
    os.symlink('/dev/null', '/etc/udev/rules.d/70-persistent-net.rules')
    os.symlink('/dev/null', '/etc/udev/rules.d/80-net-setup-link.rules')
    completestep(args, 14, "networking")

def step15_services(args, cfg):
    LOG.info(f":: Step 15: Services")
    services = args.services or []
    services += cfg.get("services", [])
    for service in services:
        if args.profile == "systemd":
            run_cmd(args, ["systemctl", "enable", service])
        else:
            run_cmd(args, ["rc-update", "add", service, "default"])
    completestep(args, 15, "services")

def step16_sysconfig(args, cfg):
    LOG.info(f":: Step 16: Sysconfig")
    if not args.pretend:
        with open("/etc/timezone", "w") as f:
            f.write("UTC")
        with open("/etc/locale.gen", "a") as f:
            f.write("en_US.UTF-8 UTF-8\nen_US ISO-8859-1\n")
        with open('/etc/sysctl.d/swappiness.conf', 'w') as f:
            f.write("vm.swappiness = 0\n")

    run_cmd(args, ["emerge", "--config", "sys-libs/timezone-data"])
    run_cmd(args, ["locale-gen"])
    run_cmd(args, ["eselect", "locale", "set", "en_US.utf8"])
    run_cmd(args, ["env-update"])
    modloadpath = os.path.join(os.sep, 'etc', 'modules-load.d')
    if not args.pretend:
        os.makedirs(modloadpath, exist_ok=True)
    if not args.pretend and args.config == "cloud.json" or args.force_cloud:
        # Maybe there's a better way to do this than a hardcoded check within the install process.
        with open(os.path.join(modloadpath, 'cloud-modules.conf'), 'w') as f:
            f.write('\n'.join(gentooimgr.config.CLOUD_MODULES))

        cloudcfg = os.path.join(os.sep, 'etc', 'cloud')
        if not os.path.exists(cloudcfg):
            os.makedirs(cloudcfg, exist_ok=True)
            os.makedirs(os.path.join(cloudcfg, 'templates'), exist_ok=True)
        with open(os.path.join(cloudcfg, 'cloud.cfg'), 'w') as cfg:
            cfg.write(f"{CLOUD_YAML}")

        os.chmod(os.path.join(cloudcfg, "cloud.cfg"), 0o644)

        with open(os.path.join(cloudcfg, "templates", "hosts.gentoo.tmpl"), 'w') as tmpl:
            tmpl.write(f"{HOST_TMPL}") # FIXME:

        os.chmod(os.path.join(cloudcfg, "templates", "hosts.gentoo.tmpl"), 0o644)

    if not args.pretend:
        os.system("sed -i 's/domain_name\,\ domain_search\,\ host_name/domain_search/g' /etc/dhcpcd.conf")
        hostname = os.path.join(os.sep, 'etc', 'conf.d', 'hostname')
        with open(hostname, 'w') as f:
            f.write(f"{HOSTNAME}\n")

        os.chmod(hostname, 0o644)
        os.remove(os.path.join(os.sep, 'etc', 'resolv.conf'))

    completestep(args, 16, "sysconfig")

def step17_fstab(args, cfg):
    LOG.info(f":: Step 17: fstab")
    partition = 1
    if not args.pretend:
        with open(os.path.join(os.sep, 'etc', 'fstab'), 'a') as fstab:
            if args.parttype == "efi":
                fstab.write(f"{cfg.get('disk')}{partition}\t/boot\tvfat\tnoatime\t1 2\n")
                partition += 1
            fstab.write(f"{cfg.get('disk')}{partition}\t/\text4\tdefaults,noatime\t0 1\n")

    completestep(args, 17, "fstab")

def step18_passwd(args, cfg):
    """Keep in mind that users that do not exist but have passwords may silently fail.
    If a user is not in /etc/shadow, the sed command will fail.
    """
    LOG.info(f":: Step 18: Setting Root Password")
    passwords = cfg.get("passwords", {})
    if passwords and not args.pretend:
        shutil.copyfile("/etc/shadow", "/root/shadow.bak")
        # https://wiki.gentoo.org/wiki/Setting_a_default_root_password
        cmd = """sed -i 's/{user}:\*/{user}\:{passwdhash}/' /etc/shadow"""
        for user, passwd in passwords.items():
            code, stdout, stderr = run_cmd(args, ["openssl", "passwd", "-6", passwd], stdout=PIPE, stderr=PIPE)

            if stderr:
                LOG.error(f"\t:: Password change for {user} contained error with return code {code}.")
                continue  # do not attempt to store a hash that fails

            passwdhash = stdout.strip()
            LOG.info(f"passwdhash {passwdhash}")
            """DEV NOTE:
                Using sed is an option, but that requires some \ escaping; hashes especially would require
                search/replacing certain characters and it's more straightforward and simple to show
                exactly what we are doing in this code snippet.
            """
            wholefile = []
            with open('/etc/shadow', 'r') as f:
                for line in f.readlines():
                    if line.startswith(user):
                        line = line.replace("*", passwdhash.decode("utf-8"))
                    wholefile.append(line)
            with open('/etc/shadow', 'w') as f:
                f.write(''.join(wholefile))  # Write it all out

    completestep(args, 18, "passwords")

def completestep(args, step, stepname, prefix='/tmp'):
    if args.step_prompt:
        input("Step Prompt: Press <Enter> to continue")
    if args.pretend:
        return
    with open(os.path.join(prefix, f"{step}.step"), 'w') as f:
        f.write("done.")  # text in this file is not currently used.
    LOG.info(f":: Step {step} {stepname} complete")


def getlaststep(prefix='/tmp'):
    i = 1
    found = False
    while not found:
        if os.path.exists(f"{i}.step"):
            i += 1
        else:
            found = True

        if i > LAST_STEP:
            break;

    LOG.info(f":: Starting off at step {i}")
    return i


def stepdone(step, prefix='/tmp'):
    return os.path.exists(os.path.join(prefix, f"{step}.step"))

def prechroot(args, cfg):
    """Work that is done pre-chroot to ensure all required files thereonin are accessible in their
    appropriate places
    """
    LOG.info("\t::Doing some pre-chroot work")
    gentooimgr.kernel.kernel_copy_conf(args, cfg, not os.path.exists('/mnt/gentoo'))
    exists = os.path.exists(cfg.get("kernel", {}).get("path", gentooimgr.kernel.DEFAULT_KERNEL_CONFIG_PATH))
    LOG.info(f"\t::Kernel configuration exists: {exists}")

def configure(args, config: dict) -> int:
    # Load configuration
    if not os.path.exists(gentooimgr.config.GENTOO_MOUNT):
        if not args.force:
            # We aren't in a gentoo live cd are we?
            LOG.error("Your system doesn't look like a gentoo live cd, exiting for safety.\n"
                "If you want to continue, use --force option and re-run `python -m gentooimgr install` with your configuration\n")
            sys.exit(gentooimgr.errorcodes.NOT_A_GENTOO_LIVE_ENV)
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
    # Move chroot out of step 9 and place it here, butcfg ensure we are at the point (or greater) where this is needed:
    if os.path.exists(gentooimgr.config.GENTOO_MOUNT):
        LOG.info(":: Binding and Mounting, Entering CHROOT")
        if not os.path.exists('/mnt/gentoo') and args.force or args.pretend:
            LOG.info(":: Using --force or --pretend, no /mnt/gentoo found so skipping chroot")

        else:
            prechroot(args, cfg)
            gentooimgr.chroot.bind()
            os.chdir(os.sep)
            os.chroot(config.get("mountpoint"))

        os.chdir(os.sep)

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
    # eth0 naming
    if not stepdone(14): step14_networking(args, cfg)
    # timezone
    # services
    if not stepdone(15): step15_services(args, cfg)
    # locale
    # set some sysctl things
    # set some dhcp things
    # hostname
    if not stepdone(16): step16_sysconfig(args, cfg)
    # fstab
    if not stepdone(17): step17_fstab(args, cfg)
    if not stepdone(18): step18_passwd(args, cfg)
    # copy cloud cfg?
    if not args.pretend: gentooimgr.chroot.unbind()
    # Finish install processes like emaint and eix-update and news read
    return gentooimgr.errorcodes.SUCCESS


