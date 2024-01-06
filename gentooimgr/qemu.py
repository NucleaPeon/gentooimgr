"""Qemu commands to run and handle the image"""
import os
import sys
import argparse
from subprocess import Popen, PIPE
import gentooimgr.config
import gentooimgr.common
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
    mounts=[]):
    """Handle mounts and run the live cd image

        - mount_isos: list of iso paths to mount in qemu as disks.
    """
    iso = config.get("iso")
    if iso is None:
        iso = gentooimgr.common.find_iso(
            os.path.join(
                os.path.abspath(os.path.dirname(__file__)),
                ".."
            )
        )

    if isinstance(iso, list):
        iso = iso[0]


    image = gentooimgr.common.get_image_name(args, config)
    qmounts = []
    mounts.extend(args.mounts)
    for i in mounts:
        qmounts.append("-drive")
        qmounts.append(f"file={i},media=cdrom")

    threads = args.threads
    cmd = [
        "qemu-system-x86_64",
        "-enable-kvm",
        "-boot", "d",
        "-m", str(config.get("memory", 2048)),
        "-smp", str(threads),
        "-drive", f"file={image},if=virtio,index=0",
        "-cdrom", iso,
        "-net", "nic,model=virtio",
        "-net", "user",
        "-vga", "virtio",
        "-cpu", "kvm64",
        "-chardev", "file,id=charserial0,path=gentoo.log",
        "-device", "isa-serial,chardev=charserial0,id=serial0",
        "-chardev", "pty,id=charserial1",
        "-device", "isa-serial,chardev=charserial1,id=serial1"
    ]
    cmd += qmounts
    LOG.debug(' '.join(cmd))
    proc = Popen(cmd, stderr=PIPE, stdout=PIPE)
    stdout, stderr = proc.communicate()
    if proc.returncode != 0:
        LOG.error(f"{stderr}")

    return proc.returncode


