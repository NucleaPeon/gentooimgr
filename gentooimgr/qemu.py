"""Qemu commands to run and handle the image"""
import os
import sys
import argparse
from subprocess import Popen, PIPE
import gentooimgr.config
import gentooimgr.common
import gentooimgr.config
import gentooimgr.errorcodes
from gentooimgr.logging import LOG


def create_image(args, config: dict, overwrite: bool = False) -> str:
    """Creates an image (.img) file using qemu that will be used to create the cloud image

    :Parameters:
        - config: dictionary/json configuration containing required information
        - overwrite: if True, run_image() will call this and re-create.


    :Returns:
        Full path to image file produced by qemu
    """

    code = gentooimgr.errorcodes.SUCCESS
    image = gentooimgr.common.get_image_name(args, config)
    name, ext = os.path.splitext(image)
    if os.path.exists(image) and not overwrite:
        return (os.path.abspath(image), code,)

    cmd = ['qemu-img', 'create', '-f', ext[1:], image, str(config.get("imgsize", "12G"))]
    LOG.info(f":: Command to create qemu image {' '.join(cmd)}")
    proc = Popen(cmd, stderr=PIPE, stdout=PIPE)
    stdout, stderr = proc.communicate()
    if proc.returncode != 0:
        LOG.error(f"{stderr}")
        code = gentooimgr.errorcodes.PROCESS_FAILED
        sys.exit(code)

    return (os.path.abspath(image), code,)

def run_image(
    args: argparse.Namespace,
    config: dict,
    mounts=[],
    livecd: bool = True):
    """Handle mounts and run the live cd image

    :Parameters:
        - args: arguments passed in from cli argument parser
        - config: dict configuration from json file
        - livecd: bool whether to include the gentoo live cd
    """
    iso = config.get("iso") if not args.iso else args.iso
    if livecd:
        iso = gentooimgr.common.find_iso(
            os.path.join(
                os.path.abspath(os.path.dirname(__file__)),
                ".."
            )
        )
        if iso and isinstance(iso, list):
            iso = iso[0]

    image = args.image
    if image is None:
        image = gentooimgr.common.get_image_name(args, config)

    LOG.debug(f"\t:: Live cd is {livecd} for image {image} and iso {iso}")
    qmounts = []
    mounts.extend(args.mounts)
    for i in mounts:
        qmounts.append("-drive")
        qmounts.append(f"file={i},media=cdrom")

    name, ext = os.path.splitext(image)
    ext = ext.strip(".")

    threads = args.threads
    cmd = [
        config.get("qemu_prog", gentooimgr.config.DEFAULT_QEMU_CMD),
        "-enable-kvm" if config.get("enable_kvm", False) else "",
        "-m", str(config.get("memory", 2048)),
        "-smp", str(threads),
        "-drive", f"file={image},if=virtio,index=0,format={ext}",
        "-net", "nic,model=virtio",
        "-net", "user",
        "-cpu", "kvm64",
        "-chardev", "file,id=charserial0,path=gentoo.log",
        "-device", "isa-serial,chardev=charserial0,id=serial0",
        "-chardev", "pty,id=charserial1",
        "-device", "isa-serial,chardev=charserial1,id=serial1"
    ]
    if config.get("vga"):
        cmd += ["-vga", config.get("vga")]
    if config.get("machine"):
        cmd += ["-M", config.get("machine")]
    if config.get("bios"):
        cmd += ["-L", config.get("bios")]
    if iso:
        cmd += ["-drive", f"file={iso},format=raw", "-boot", "d"]  # Boot the first CD-ROM
    else:
        cmd += ["-boot", "c"]  # Boot first hard drive

    if args.parttype == 'efi':
        cmd += ["-bios", args.efi_firmware]
        cmd += config.get("qemu_cmd", ['-drive', f'file={args.efi_firmware},if=pflash,format=raw,unit=0,readonly=on'])

    cmd += qmounts
    LOG.debug(' '.join(cmd))
    proc = Popen(cmd, stderr=PIPE, stdout=PIPE)
    stdout, stderr = proc.communicate()
    if proc.returncode != 0:
        LOG.error(f"{stderr}")

    return proc.returncode


