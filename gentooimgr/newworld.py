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
    part = partition.lstrip("/dev/")
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
    part = partition.lstrip("/dev/")
    for _o in output:
        if part in _o:
            stripped = [ __o for __o in _o.split(" ") if __o]
            major, minor, blocks, name = stripped
            major = int(major)
            minor = int(minor)
            blocks = int(blocks)
            return blocks*2  # we go from 1024-sized blocks to 512

if __name__ == "__main__":
    # Set up partition with all required settings

    partition = "/dev/sda"
    blocks = calc_device_blocks(partition)
    print(blocks)
    ram = os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")
    print(ram/512)

    # LEFT OFF:
    # need to calculate how to get things like bytes/kb/mb/gb to block sizes, and as things progress, keep tabs on start/end blocks and add to total

    sys.exit(0)

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
    _bytes = 800.0 * 1024  # kilobytes, not kibibytes
    currentblk += _bytes/512  # 800k in blocks plus previous blocks, 1600 blocks

    child.sendline("c")
    child.expect("First block:")
    child.sendline(currentblk+1)
    child.expect("Length (in blocks, kB (k), MB (M) or GB (G)):")
    _bytes = 512 * 1024 * 1024  # We default to 512M boot partition
    _blocks = _bytes/512
    child.sendline(_blocks)
    currentblk += _blocks
    child.expect("Name of partition:")
    child.sendline("boot")


    child.sendline("c")
    child.expect("First block:")
    child.sendline(currentblk+1)
    child.expect("Length (in blocks, kB (k), MB (M) or GB (G)):")
    # Swap will be size of physical ram
    _bytes = os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")
    _blocks = _bytes/512
    child.sendline(_blocks)
    currentblk += _blocks
    child.expect("Name of partition:")
    child.sendline("swap")

    child.sendline("c")
    child.expect("First block:")
    child.sendline(currentblk+1)
    child.expect("Length (in blocks, kB (k), MB (M) or GB (G)):")
    _blocks = blocks-currentblk  # Use the rest
    child.sendline(_blocks)
    currentblk += _blocks
    child.expect("Name of partition:")
    child.sendline("rootfs")
