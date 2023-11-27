"""Qemu commands to run and handle the image"""
import os
import sys
from subprocess import Popen, PIPE
import gentooimgr.config

def create_image(image: str = "gentoo.img", fmt: str = "qcow2", size: str = gentooimgr.config.QEMU_IMG_SIZE,
                 overwrite: bool = False) -> str:
    """Creates an image (.img) file using qemu that will be used to create the cloud image

    :Parameters:
        - image: desired name for the cloud image file
        - fmt: format, defaults to qcow2
        - size: string with a size suffixed with size denomination, usually G for gigabyte
        - overwrite: if True, run_image() will call this and re-create.


    :Returns:
        Full path to image file produced by qemu
    """
    fname, ext = os.path.splitext(image)
    image = fname + f".{fmt}"  # Replace extension with our format so we know what we're getting
    if os.path.exists(image) and not overwrite:
        return os.path.abspath(image)

    proc = Popen(['qemu-img', 'create', '-f', fmt, image, size],
                 stderr=PIPE, stdout=PIPE)
    stdout, stderr = proc.communicate()
    return os.path.abspath(image)

def run_image(
    args,
    iso=None,
    mounts=[],  # Additional mounts besides what's passed into args
    memory: int = gentooimgr.config.QEMU_MEMORY,
    threads: int = gentooimgr.config.THREADS):
    """Handle mounts and run the live cd image

        - mount_isos: list of iso paths to mount in qemu as disks.
    """
    if iso is None:
        iso = gentooimgr.common.find_iso(
            os.path.join(
                os.path.abspath(os.path.dirname(__file__)),
                ".."
            )
        )
        if iso:
            iso = iso[0]  # this returns a list
    qmounts = []
    mounts.extend(args.mounts)
    for i in mounts:
        qmounts.append("-drive")
        qmounts.append(f"file={i},media=cdrom")

    cmd = [
        "qemu-system-x86_64",
        "-enable-kvm",
        "-boot", "d",
        "-m", str(memory),
        "-smp", str(args.threads),
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

