"""Configure a Gentoo guest with cloud image settings

This step keeps track of how far it's gotten, so re-running this command
will continue on if an error was to occur, unless --start-over flag is given.
"""

import os
import sys
from subprocess import Popen, PIPE
import gentooimgr.config
import gentooimgr.common
import gentooimgr.chroot
import gentooimgr.kernel

CLOUD_YAML = """
# The top level settings are used as module
# and system configuration.

# A set of users which may be applied and/or used by various modules
# when a 'default' entry is found it will reference the 'default_user'
# from the distro configuration specified below
users:
   - default

# If this is set, 'root' will not be able to ssh in and they
# will get a message to login instead as the above $user (ubuntu)
disable_root: true
ssh_pwauth:   false

# This will cause the set+update hostname module to not operate (if true)
preserve_hostname: false

# this may be helpful in certain scenarios
# resize_rootfs_tmp: /dev

syslog_fix_perms: root:root

ssh_deletekeys: false
ssh_genkeytypes: [rsa, dsa]

# This can be 'template'
# which would look for /etc/cloud/templates/hosts.gentoo.tmpl
# or 'localhost'
# or False / commented out to disable altogether
manage_etc_hosts: template

# Example datasource config
# datasource:
#    Ec2:
#      metadata_urls: [ 'blah.com' ]
#      timeout: 5 # (defaults to 50 seconds)
#      max_wait: 10 # (defaults to 120 seconds)

# The modules that run in the 'init' stage
cloud_init_modules:
 - seed_random
 - bootcmd
 - write-files
 - growpart
 - resizefs
 - set_hostname
 - update_hostname
 - update_etc_hosts
 - ca-certs
 - users-groups
 - ssh

# The modules that run in the 'config' stage
cloud_config_modules:
# Emit the cloud config ready event
# this can be used by upstart jobs for 'start on cloud-config'.
 - disk_setup
 - mounts
 - ssh-import-id
 - set-passwords
 - package-update-upgrade-install
 - timezone
 - puppet
 - chef
 - salt-minion
 - mcollective
 - disable-ec2-metadata
 - runcmd

# The modules that run in the 'final' stage
cloud_final_modules:
 - scripts-vendor
 - scripts-per-once
 - scripts-per-boot
 - scripts-per-instance
 - scripts-user
 - ssh-authkey-fingerprints
 - keys-to-console
 - phone-home
 - final-message
 - power-state-change

# System and/or distro specific settings
# (not accessible to handlers/transforms)
system_info:
   # This will affect which distro class gets used
   distro: gentoo
   # Default user name + that default users groups (if added/used)
   default_user:
     name: gentoo
     lock_passwd: True
     gecos: Gentoo
     groups: [users, wheel]
     primary_group: users
     no-user-group: true
     sudo: ["ALL=(ALL) NOPASSWD:ALL"]
     shell: /bin/bash
   # Other config here will be given to the distro class and/or path classes
   paths:
      cloud_dir: /var/lib/cloud/
      templates_dir: /etc/cloud/templates/
"""

HOST_TMPL = """
## template:jinja
{#
This file /etc/cloud/templates/hosts.gentoo.tmpl is only utilized
if enabled in cloud-config.  Specifically, in order to enable it
you need to add the following to config:
  manage_etc_hosts: template
-#}
# Your system has configured 'manage_etc_hosts' as 'template'.
# As a result, if you wish for changes to this file to persist
# then you will need to either
# a.) make changes to the master file in /etc/cloud/templates/hosts.gentoo.tmpl
# b.) change or remove the value of 'manage_etc_hosts' in
#     /etc/cloud/cloud.cfg or cloud-config from user-data
#
# The following lines are desirable for IPv4 capable hosts
127.0.0.1 {{fqdn}} {{hostname}}
127.0.0.1 localhost.localdomain localhost
127.0.0.1 localhost4.localdomain4 localhost4

# The following lines are desirable for IPv6 capable hosts
::1 {{fqdn}} {{hostname}}
::1 localhost.localdomain localhost
::1 localhost6.localdomain6 localhost6
"""

HOSTNAME = """
# Set to the hostname of this machine
if [ -f /etc/hostname ];then
    hostname=$(cat /etc/hostname 2> /dev/null | cut -d"." -f1 2> /dev/null)
else
    hostname="localhost"
fi
"""


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
    proc = Popen(["mount", f'{cfg.get("disk")}{cfg.get("partition")}', gentooimgr.config.GENTOO_MOUNT])
    proc.communicate()
    completestep(2, "mount")

def step3_stage3(args, cfg):
    print(f'\t:: Step 3: Stage3 Tarball')
    proc = Popen(["tar", "xpf", cfg.get("stage3"), "--xattrs-include='*.*'", "--numeric-owner", "-C",
                  f'{gentooimgr.config.GENTOO_MOUNT}'])
    proc.communicate()
    completestep(3, "stage3")

def step4_binds(args, cfg):
    print(f'\t:: Step 4: Binding Filesystems')
    gentooimgr.chroot.bind(verbose=False)
    completestep(4, "binds")

def step5_portage(args, cfg):
    print(f'\t:: Step 5: Portage')
    proc = Popen(["tar", "xpf", args.portage or cfg.get("portage"), "-C", f"{gentooimgr.config.GENTOO_MOUNT}/usr/"])
    proc.communicate()
    completestep(5, "portage")

def step6_licenses(args, cfg):
    print(f'\t:: Step 6: Licenses')
    license_path = os.path.join(gentooimgr.config.GENTOO_MOUNT, 'etc', 'portage', 'package.license')
    os.makedirs(license_path, exist_ok=True)
    for f, licenses in gentooimgr.config.GENTOO_ACCEPT_LICENSE.items():
        with open(os.path.join(license_path, f), 'w') as f:
            f.write('\n'.join(licenses))
    completestep(6, "license")

def step7_repos(args, cfg):
    print(f'\t:: Step 7: Emerge Sync Repo')
    repo_path = os.path.join(gentooimgr.config.GENTOO_MOUNT, 'etc', 'portage', 'repos.conf')
    os.makedirs(repo_path)
    with open(os.path.join(repo_path, 'gentoo.conf'), 'w') as f:
        f.write(gentooimgr.config.GENTOO_REPO_FILE)

    completestep(7, "repos")

def step8_resolv(args, cfg):
    print(f'\t:: Step 8: Resolv')
    proc = Popen(["cp", "--dereference", "/etc/resolv.conf", os.path.join(gentooimgr.config.GENTOO_MOUNT, 'etc')])
    proc.communicate()
    # Copy all step files and python module to new chroot
    os.system(f"cp /tmp/*.step {gentooimgr.config.GENTOO_MOUNT}/tmp")
    os.system(f"cp -r /mnt/gi {gentooimgr.config.GENTOO_MOUNT}/mnt/")
    completestep(8, "resolv")

def step9_sync(args, cfg):
    print(f"\t:: Step 9: sync")
    print("\t\t:: Entering chroot")
    os.chroot(gentooimgr.config.GENTOO_MOUNT)
    os.chdir(os.sep)

    proc = Popen(["emerge", "--sync", "--quiet"])
    proc.communicate()
    completestep(9, "sync")

def step10_emerge_pkgs(args, cfg):
    print(f"\t:: Step 10: emerge pkgs")
    for oneshot_up in gentooimgr.config.ONESHOT_UPDATE_PKGS:
        proc = Popen(["emerge", "--oneshot", "--update", oneshot_up])
        proc.communicate()

    for single in gentooimgr.config.EMERGE_SINGLE_PKGS:
        proc = Popen(["emerge", single])
        proc.communicate()

    for keepgoing in gentooimgr.config.EMERGE_KEEP_GOING_PKGS:
        proc = Popen(["emerge", keepgoing])
        proc.communicate()

    cmd = ["emerge", "-j", str(gentooimgr.config.THREADS), "--keep-going"]
    cmd += gentooimgr.config.KERNEL_PACKAGES if not args.dist_kernel else ['sys-kernel/gentoo-kernel-bin']
    cmd += gentooimgr.config.BASE_PACKAGES
    cmd += gentooimgr.config.ADDITIONAL_PACKAGES
    cmd += gentooimgr.config.BOOTLOADER_PACKAGES
    proc = Popen(cmd)
    proc.communicate()
    completestep(10, "pkgs")

def step11_kernel(args, cfg):
    # at this point, genkernel will be installed
    print(f"\t:: Step 11: kernel")
    proc = Popen(["eselect", "kernel", "set", "1"])
    proc.communicate()
    if not args.dist_kernel:
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
    proc = Popen(["sed", "-i", "'s/^#s0:/s0:/g'","/etc/inittab"])
    proc.communicate()
    proc = Popen(["sed", "-i", "'s/^#s1:/s1:/g'","/etc/inittab"])
    proc.communicate()
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
        f.write('\n'.join(gentooimgr.config.CLOUD_MODULES))

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

def configure(args):
    # Load configuration
    if not os.path.exists(gentooimgr.config.GENTOO_MOUNT):
        if not args.force:
            # We aren't in a gentoo live cd are we?
            sys.stderr.write("Your system doesn't look like a gentoo live cd, exiting for safety.\n"
                "If you want to continue, use --force option and re-run `python -m gentooimgr cloud-cfg`\n")
            sys.exit(1)

        else:
            # Assume we are root as per live cd, otherwise user should run this as root as a secondary confirmation
            os.makedirs(gentooimgr.config.GENTOO_MOUNT)
    # disk prep
    cfg = gentooimgr.common.load_config(args)
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


