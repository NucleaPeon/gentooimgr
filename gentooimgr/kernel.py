import os
import sys
import re
import shutil
import datetime
from subprocess import Popen, PIPE
import time

import gentooimgr.configs

DEFAULT_KERNEL_CONFIG_PATH = os.path.join(os.sep, 'etc', 'kernel', 'default.config')

def kernel_conf_apply(args, config):
    """Kernel configuration is a direct copy of a full complete config file"""
    fname, ext = os.path.splitext(args.config)
    # Default is the json file's name but with .config extension.
    kernelconfig = os.path.join(gentooimgr.configs.CONFIG_DIR,
                                config.get("kernel", {}).get("config", f"{fname}.config"))
    kernelpath = config.get("kernel", {}).get("path", DEFAULT_KERNEL_CONFIG_PATH)
    if os.path.exists(kernelpath):
        os.remove(kernelpath)
    else:
        # Ensure if we have directories specified that they exist
        os.makedirs(os.path.dirname(kernelpath), exist_ok=True)

    shutil.copyfile(kernelconfig, kernelpath)

def build_kernel(args, config):
    if config.get("kernel", {}).get("config") is None:
        kernel_default_config(args, config)
    os.chdir(args.kernel_dir)
    kernelpath = config.get("kernel", {}).get("path", DEFAULT_KERNEL_CONFIG_PATH)
    kernel_conf_apply(args, config)
    proc = Popen(['genkernel', f'--kernel-config={kernelpath}', '--save-config', '--no-menuconfig', 'all'])
    proc.communicate()
    kernel_save_config(args, config)

def kernel_default_config(args, config):
    os.chdir(args.kernel_dir)
    proc = Popen(["make", "defconfig"])
    proc.communicate()

def kernel_save_config(args, config):
    os.chdir(args.kernel_dir)
    """Saves the current .config file"""
    proc = Popen(["make", "savedefconfig"])
    proc.communicate()

GRUB_CFG = """
# Copyright 1999-2015 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: /var/cvsroot/gentoo-x86/sys-boot/grub/files/grub.default-3,v 1.5 2015/03/25 01:58:00 floppym Exp $
#
# To populate all changes in this file you need to regenerate your
# grub configuration file afterwards:
#     'grub2-mkconfig -o /boot/grub/grub.cfg'
#
# See the grub info page for documentation on possible variables and
# their associated values.

GRUB_DISTRIBUTOR="Gentoo"

# Default menu entry
#GRUB_DEFAULT=0

# Boot the default entry this many seconds after the menu is displayed
#GRUB_TIMEOUT=5
#GRUB_TIMEOUT_STYLE=menu

# Append parameters to the linux kernel command line
# openrc only spits to the last console=tty
GRUB_CMDLINE_LINUX="net.ifnames=0 vga=791 console=tty0 console=ttyS0,115200"
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
GRUB_TERMINAL="serial console"
GRUB_SERIAL_COMMAND="serial --speed=115200"
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
