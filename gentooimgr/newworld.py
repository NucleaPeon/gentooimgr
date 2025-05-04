"""Module for handling newworld mac procesess automatically even though they are interactive
"""
import os
import sys
import pexpect
import fcntl
from gentooimgr.process import run

def calc_device_size(blockdev):
    # 512 block size in mac-fstab, 1024 in /proc/partitions!
    code, o, e = run(['cat', '/proc/partitions'])
    output = str(o).split("\\n")
    part = blockdev.lstrip("/dev/")
    for _o in output:
        if part in _o:
            stripped = [ __o for __o in _o.split(" ") if __o]
            major, minor, blocks, name = stripped
            major = int(major)
            minor = int(minor)
            blocks = int(blocks)
            return (blocks*1024.0)/(2**30)
            # end loop, so if somehow sda and sda1 occur in /proc/partitions,
            # we don't use a partition instead of device.

def calc_device_blocks(blockdev):
    code, o, e = run(['cat', '/proc/partitions'])
    output = str(o).split("\\n")
    part = blockdev.lstrip("/dev/")
    for _o in output:
        if part in _o:
            stripped = [ __o for __o in _o.split(" ") if __o]
            major, minor, blocks, name = stripped
            major = int(major)
            minor = int(minor)
            blocks = int(blocks)
            return blocks*2  # we go from 1024-sized blocks to 512

def write_partition(partition):
    """ Writes the new world mac partition scheme to disk.
    While this may be extended later, it will default to a
    512 Mb Grub partition, a swap partition the same size as one's RAM,
    and the rest as the rootfs partition.

    partition parameter is typically "/dev/sda"
    """
    blocks = calc_device_blocks(partition)

    currentblk = 63  # This is the Apple_partition_map size
    child = pexpect.spawn("mac-fdisk /dev/sda")
    child.expect("/dev/sda")
    child.sendline("i")
    part_exists = "map already exists"
    part_empty = "size of 'device' is"
    child.expect([part_exists, part_empty])
    if part_exists.encode() in child.after:
        child.sendline("y")

    child.sendline(f"{blocks}")
    child.expect("new size of 'device' is")
    child.sendline("b")
    child.expect("First block:")
    child.sendline(f"{currentblk+1}")
    _bytes = 800 * 1024  # kilobytes, not kibibytes
    currentblk += int(_bytes/512)  # 800k in blocks plus previous blocks, 1600 blocks

    child.sendline("c")
    child.expect("First block:")
    child.sendline(f"{currentblk+1}")
    child.expect("Length")
    _bytes = 512 * 1024 * 1024  # We default to 512M boot partition
    _blocks = int(_bytes/512)
    child.sendline(f"{_blocks}")
    currentblk += _blocks
    child.expect("Name of partition:")
    child.sendline("boot")

    child.sendline("c")
    child.expect("First block:")
    child.sendline(f"{currentblk+1}")
    child.expect("Length")
    # Swap will be size of physical ram
    _bytes = os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")
    _blocks = int(_bytes/512)
    child.sendline(f"{_blocks}")
    currentblk += _blocks
    child.expect("Name of partition:")
    child.sendline("swap")

    child.sendline("c")
    child.expect("First block:")
    child.sendline(f"{currentblk+1}")
    child.expect("Length")
    _blocks = blocks-currentblk  # Use the rest
    child.sendline(f"{_blocks}")
    currentblk += _blocks
    child.expect("Name of partition:")
    child.sendline("rootfs")

    child.sendline("w")
    child.sendline("y")


def setup_hfs_bootloader(hfsbootloader):
    code, o, e = run(['dd' , 'if=/dev/zero', f'of={hfsbootloader}', 'bs=512'])
    code, o, e = run(['hformat', '-l', 'bootstrap', hfsbootloader])
    tmpdir = os.path.join(os.sep, 'tmp', 'bootstrap')
    os.makedirs(tmpdir, exist_ok=True)
    code, o, e = run(['mount', '-t', 'hfs', hfsbootloader, tmpdir])
    code, o, e = run(['grub-install', f'--macppc-directory={tmpdir}'])
    code, o, e = run(['umount', hfsbootloader, tmpdir])


def hfs_bless(hfsbootloader):
    code, o, e = run(['hmount', hfsbootloader])
    code, o, e = run(['hattrib', '-t', 'tbxi', '-c', 'UNIX', ":System:Library:CoreServices:BootX"])
    code, o, e = run(['hattrib', '-b', ":System:Library:CoreServices"])
    code, o, e = run(['humount'])

def newworldmac_grub():
    #
    contents = ""
    with open(os.path.join(os.sep, 'etc', 'default', 'grub'), 'r') as grub:
        contents = grub.read()

    contents.replace("#GRUB_TIMEOUT=5", "GRUB_TIMEOUT=3")
    contents.replace("#GRUB_TIMEOUT_STYLE=menu", "GRUB_TIMEOUT_STYLE=menu")
    # nouveau.modeset=0
    contents.replace('#GRUB_CMDLINE_LINUX=""', 'GRUB_CMDLINE_LINUX="rootfstype=ext4"')
    if not "GRUB_PRELOAD_MODULES" in contents:
        contents += """\nGRUB_PRELOAD_MODULES="ieee1275_fb linux normal eval memdisk read test test_blockarg trig true"\n"""

    with open(os.path.join(os.sep, 'etc', 'default', 'grub'), 'w') as grub:
        grub.write(contents)

    code, o, e = run(['grub-mkconfig', '-o', '/boot/grub/grub.cfg'])
