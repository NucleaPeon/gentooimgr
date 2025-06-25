import os
import sys
import re
import shutil
import datetime
from subprocess import Popen, PIPE
import time

import gentooimgr.configs
from gentooimgr.process import run_cmd
from gentooimgr.logging import LOG
import gentooimgr.errorcodes
DEFAULT_KERNEL_CONFIG_PATH = os.path.join(os.sep, 'etc', 'kernel', 'default.config')

def get_kernel_config_name(args, config):
    """Retrieve the expected name of our kernel .config equivalent file.
        * --config-cloud = cloud
        * --config-qemu  = qemu
        etc.

        Returns without the suffix.
    """
    kernelconf = config.get("kernel", {}).get("config") or args.config
    if kernelconf is None:
        return None
    f, ext = os.path.splitext(kernelconf)  # args.config may have .json extension
    name = os.path.basename(f)
    return f"gentooimgr-{name}"

def get_base_config_name(args, config):
    kernelconf = config.get("kernel", {}).get("config") or args.config
    if kernelconf is None:
        return None
    f, ext = os.path.splitext(kernelconf)  # args.config may have .json extension
    name = os.path.basename(f)
    return name

def get_installed_kernel_config_path(args, config, inchroot):
    """Using get_kernel_config_name(), get the installed file path to the kernel file.
    Ex: cloud.config would be /etc/kernels/config.d/gentooimgr-cloud.config

    We prepend 'gentooimgr' for explicit readability.
    """
    name = get_kernel_config_name(args, config)
    LOG.info(f"Kernel name {name}")
    kerneldir = os.path.join(os.sep, 'mnt', 'gentoo', 'etc', 'kernels', 'config.d') if not inchroot else os.path.join(os.sep, 'etc', 'kernels', 'config.d')
    LOG.info(f"Kernel dir {kerneldir}")
    # Explicitly prefer the supplied --config arg if given
    try:
        kconf = args.kconf
    except AttributeError as aE:
        kconf = os.path.join(kerneldir, f'{name}.config')
    return kconf

def kernel_copy_conf(args, config, inchroot=False) -> int:
    """Copies our *.config file into /etc/kernels/config.d/[name].config.
    """
    code = gentooimgr.errorcodes.PROCESS_FAILED
    if inchroot:
        LOG.warning("\t:: Kernel cannot copy gentooimgr config files while in chroot, lost access. This may not work")
    if os.path.exists(gentooimgr.configs.CONFIG_DIR):
        kernelconf = get_installed_kernel_config_path(args, config, inchroot)
        path = os.path.dirname(kernelconf)
        LOG.debug(f"\t:: Creating kernel configuration path {path}")
        os.makedirs(path, exist_ok=True)

        configfile = os.path.join(gentooimgr.configs.CONFIG_DIR, f"{get_base_config_name(args, config)}.config")
        LOG.info(f"\t:: Looking for kernel configuration file {configfile}: {os.path.exists(configfile)}")
        if os.path.exists(configfile):
            LOG.debug(f"\t:: Config file {configfile} exists.")
            shutil.copyfile(configfile, kernelconf)
            code = gentooimgr.errorcodes.SUCCESS

        else:
            LOG.debug(f"\t:: Config file {configfile} does not exist!")
    else:
        LOG.error(f"{gentooimgr.configs.CONFIG_DIR} does not exist. Chroot: {inchroot}")

    return code

def chdir_kerneldir(args, inchroot=False):
    kerneldir = args.kernel_dir
    if not inchroot:
        if kerneldir[0] == os.sep:
            kerneldir = kerneldir[1:] # remove '/' from
        kerneldir = os.path.join(os.sep, 'mnt', 'gentoo', kerneldir)
    LOG.info(f"::\t Chdir'ing to kernel directory {kerneldir} ({'in chroot' if inchroot else 'not in chroot'})")
    os.chdir(kerneldir)

""" Entrypoint from install.py """
def build_kernel(args, config, inchroot=False) -> int:
    code = gentooimgr.errorcodes.SUCCESS
    if args.kernel_dist:
        # Distribution kernel builds itself so the package step handles this.
        LOG.warning("--kernel-dist is enabled so no actual build is performed here; "
            "Running `emerge sys-kernel/gentoo-kernel-bin` will install the kernel "
            "if you want this done in its own step.")

        return code

    kerneldir = args.kernel_dir
    LOG.info(f"::\t Kernel dir {kerneldir}")
    chdir_kerneldir(args, inchroot=inchroot)
    # kernel_copy_conf needs to happen before this works correctly:
    kernel_copy_conf(args, config, inchroot=inchroot)
    kernelconf = get_installed_kernel_config_path(args, config, inchroot)
    LOG.info(f"::\t Using kernel configuration {'default' if kernelconf is None else kernelconf}")
    if kernelconf is None:
        kernel_default_config(args, config)

    cmd = []
    has_genkernel = False
    for pkg in config.get("packages", {}).get("kernel", []):
        LOG.debug(f"\t:: Kernel package {pkg}")
        if "genkernel" in pkg:
            has_genkernel = True
            cmd = ['genkernel', f'--kernel-config={kernelconf}', '--no-menuconfig']

            if args.parttype == "efi":
                cmd.append( '--bootdir=/boot/efi' )
            if config.get("vga", "") == "virtio":
                cmd.append(  '--virtio' )

            cmd.append("all")
            code, stdout, stderr = run_cmd(args, cmd)

    if not has_genkernel:
        chdir_kerneldir(args)
        shutil.copyfile(kernelconf, '.config')
        for cmd in [['make'], ['make', 'modules_install'], ['make', 'install']]:
            code, stdout, stderr = run_cmd(args, cmd)

    return code

def kernel_default_config(args, config):
    code = gentooimgr.errorcodes.SUCCESS
    os.chdir(args.kernel_dir)
    code, stdout, stderr = run_cmd(args, ["make", "defconfig"])
    if code != 0:
        LOG.error(f"kernel command `make defconfig` failed")

    try:
        code, stdout, stderr = run_cmd(args, ["make", "kvm_guest.config"])
        if code != 0:
            LOG.error(f"kernel command `make defconfig` failed")
    except:
        LOG.warning("`make kvm_guest.config failed, if this is a kernel version <= 5.10, attempting make kvmconfig")
        code, stdout, stderr = run_cmd(args, ["make", "kvmconfig"])
        if code != 0:
            LOG.error("kernel command `make kvmconfig` failed")

    return code

def kernel_save_config(args, config):
    code = gentooimgr.errorcodes.SUCCESS
    os.chdir(args.kernel_dir)
    """Saves the current .config file"""
    code, stdout, stderr = run_cmd(args, ["make", "savedefconfig"])
    if code != 0:
        LOG.warning(f"kernel command `{' '.join(cmd)}` failed")
        # Return proper error code, but don't necessarily exit.
        code = gentooimgr.errorcodes.PROCESS_FAILED

    return code

def gen_grub_cfg(cli, use_serial=True):
    return f"""# Copyright 1999-2015 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: /var/cvsroot/gentoo-x86/sys-boot/grub/files/grub.default-3,v 1.5 2015/03/25 01:58:00 floppym Exp $
#
# To populate all changes in this file you need to regenerate your
# grub configuration file afterwards:
#     'grub2-mkconfig -o /boot/grub/grub.cfg'
#
# See the grub info page for documentation on possible variables and
# their associated values.

GRUB_DISTRIBUTOR="GentooImgr"

# Default menu entry
#GRUB_DEFAULT=0

# Boot the default entry this many seconds after the menu is displayed
GRUB_TIMEOUT=5
GRUB_TIMEOUT_STYLE=menu

# Append parameters to the linux kernel command line
# openrc only spits to the last console=tty
GRUB_CMDLINE_LINUX="{cli}"
#
# Examples:
#
# Boot with network interface renaming disabled
# GRUB_CMDLINE_LINUX="net.ifnames=0"
#
# Boot with systemd instead of sysvinit (openrc)
# GRUB_CMDLINE_LINUX="init=/usr/lib/systemd/systemd"

# Append parameters to the linux kernel command line for non-recovery entries
#GRUB_CMDLINE_LINUX_DEFAULT=""

# Uncomment to disable graphical terminal (grub-pc only)
{'#' if not use_serial else ''} GRUB_TERMINAL="serial console"
{'#' if not use_serial else ''} GRUB_SERIAL_COMMAND="serial --speed=115200"
#GRUB_SERIAL_COMMAND="serial --speed=115200 --unit=0 --word=8 --parity=no --stop=1"

# The resolution used on graphical terminal.
# Note that you can use only modes which your graphic card supports via VBE.
# You can see them in real GRUB with the command `vbeinfo'.
#GRUB_GFXMODE=640x480

# Set to 'text' to force the Linux kernel to boot in normal text
# mode, 'keep' to preserve the graphics mode set using
# 'GRUB_GFXMODE', 'WIDTHxHEIGHT'['xDEPTH'] to set a particular
# graphics mode, or a sequence of these separated by commas or
# semicolons to try several modes in sequence.
#GRUB_GFXPAYLOAD_LINUX=

# Path to theme spec txt file.
# The starfield is by default provided with use truetype.
# NOTE: when enabling custom theme, ensure you have required font/etc.
#GRUB_THEME="/boot/grub/themes/starfield/theme.txt"

# Background image used on graphical terminal.
# Can be in various bitmap formats.
#GRUB_BACKGROUND="/boot/grub/mybackground.png"

# Uncomment if you don't want GRUB to pass "root=UUID=xxx" parameter to kernel
#GRUB_DISABLE_LINUX_UUID=true

# Uncomment to disable generation of recovery mode menu entries
#GRUB_DISABLE_RECOVERY=true

# Uncomment to disable generation of the submenu and put all choices on
# the top-level menu.
# Besides the visual affect of no sub menu, this makes navigation of the
# menu easier for a user who can't see the screen.
GRUB_DISABLE_SUBMENU=y

# Uncomment to play a tone when the main menu is displayed.
# This is useful, for example, to allow users who can't see the screen
# to know when they can make a choice on the menu.
#GRUB_INIT_TUNE="60 800 1"

"""
