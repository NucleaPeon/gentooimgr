"""Qemu commands to run and handle the image"""
import os
import sys
import argparse
from subprocess import Popen, PIPE
import gentooimgr.config

def create_image(config: dict, overwrite: bool = False) -> str:
    """Creates an image (.img) file using qemu that will be used to create the cloud image

    :Parameters:
        - config: dictionary/json configuration containing required information
        - overwrite: if True, run_image() will call this and re-create.


    :Returns:
        Full path to image file produced by qemu
    """

    image = config.get("imagename")
    name, ext = os.path.splitext(config_name)
    if os.path.exists(image) and not overwrite:
        return os.path.abspath(image)

    proc = Popen(['qemu-img', 'create', '-f', ext, image, str(config.get("memory", 2048))],
                 stderr=PIPE, stdout=PIPE)
    stdout, stderr = proc.communicate()
    return os.path.abspath(image)

def run_image(
    args: argparse.Namespace,
    config: dict,
    mounts=[]):
    """Handle mounts and run the live cd image

        - mount_isos: list of iso paths to mount in qemu as disks.
    """
    iso = config.get(
        "iso",
        gentooimgr.common.find_iso(
            os.path.join(
                os.path.abspath(os.path.dirname(__file__)),
                ".."
            )
        )
    )
    if isinstance(iso, list):
        iso = iso[0]

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
        "-drive", f"file={args.image},if=virtio,index=0",
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
    print(' '.join(cmd))
    cmd.extend(qmounts)
    proc = Popen(cmd, stderr=PIPE, stdout=PIPE)
    proc.communicate()

