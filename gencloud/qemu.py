"""Qemu commands to run and handle the image"""
import os
from subprocess import Popen, PIPE
import gencloud.config as config

def create_image(image: str = "gentoo.img", fmt: str = "qcow2", size: str = "10G") -> str:
    """Creates an image (.img) file using qemu that will be used to create the cloud image

    :Parameters:
        - image: desired name for the cloud image file
        - fmt: format, defaults to qcow2
        - size: string with a size suffixed with size denomination, usually G for gigabyte


    :Returns:
        Full path to image file produced by qemu
    """

    proc = Popen(['qemu-img', 'create', '-f', fmt, image, size],
                 stderr=PIPE, stdout=PIPE)
    stdout, stderr = proc.communicate()
    return os.path.abspath(image)

def run_image(
    gentoolivecd: str,
    image: str = "gentoo.img",
    memory: int = config.QEMU_MEMORY,
    threads: int = config.THREADS,
    mount_isos: list = []):
    """Handle mounts and run the live cd image

        - mount_isos: list of iso paths to mount in qemu as disks.
    """

    mounts = []
    for iso in mount_isos:
        mounts.append("-drive")
        mounts.append(f"file={iso},media=cdrom")

    cmd = [
        "qemu-system-x86_64",
        "-enable-kvm",
        "-m", str(memory),
        "-smp", str(threads),
        "-drive", f"file={image},if=virtio,index=0",
        "-cdrom", gentoolivecd,
        "-net", "nic,model=virtio",
        "-net", "user",
        "-vga", "virtio",
        "-cpu", "kvm64",
        "-chardev", "file,id=charserial0,path=gentoo.img.log",
        "-device", "isa-serial,chardev=charserial0,id=serial0",
        "-chardev", "pty,id=charserial1",
        "-device", "isa-serial,chardev=charserial1,id=serial1"
    ] + mounts
    proc = Popen(cmd, stderr=PIPE, stdout=PIPE)
    proc.communicate()

