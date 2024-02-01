# GentooImgr: Gentoo Image Builder for Cloud and Turnkey ISO installers


GentooImgr is a python script system to build cloud images based on Gentoo Linux.

Huge thanks to https://github.com/travisghansen/gentoo-cloud-image-builder for providing a foundation to work from.


**Features:**

* This project enables easy access to building ``systemd`` or ``openrc`` -based images.
* Performs automatic download AND verification of the linux iso, stage3 tarball and portage.
* Caches the iso and stage3 .txt files for at most a day before redownloading and rechecking for new files
* Sane and readable cli commands to build, run and test.
* Step system to enable user to continue off at the same place if a step fails
* No heavy packages like rust included ** Cloud Init images do require rust, QEMU-only doesn't. (TODO)

## Preface

This project was created so I could spawn off Gentoo OS templates on my Proxmox server for various services while being more efficient than many other Linux OS's and avoiding systemd.

This python module contains all the software needed to download resources, build the image, run the image in qemu, and allow for some extensibility. The built-in functionality includes a base standard gentoo image configuration as well as a cloud-init image that can be run. You can copy the .json config file and optionally a kernel .config file to configure your image to your liking and pass it in with ``--config``.

This software is in beta so please report any issues or feature requests. You are **highly** encouraged to do so.

Thanks!

## Roadmap

* [X] Use gentooimgr to configure and Install a Base Gentoo OS using the least amount of configuration
* [X] Use gentooimgr to create a usable cloud image without a binary dist kernel
* [ ] Use gentooimgr to create Gentoo installations on other non-amd64/non-native architectures (ex: ppc64)
* [ ] Allow better handling from image building third party software such as ansible and terraform
* [ ] Build turnkey (LXC) images

## Prerequisites

* [ ] QEMU
* [ ] python3.11
* [ ] Recommended 20GB of space
* [ ] Internet Connection
* [ ] virt-sparsify (for use with `gentooimgr shrink` action, optional)
* [ ] OVMF firmware for using EFI enabled images (optional)



## Quick Start

```sh
git clone https://github.com/NucleaPeon/gentooimgr.git
python -m gentooimgr build
python -m gentooimgr run
```

Once qemu is running, mount the available gentooimgr iso and run the appropriate command:

```sh
mkdir -p /mnt/gi
mount /dev/disk/by-label/gentooimgr /mnt/gi
cd /mnt/gi
python -m gentooimgr --config-cloud install
python -m gentooimgr unchroot
```

### Using EFI

This is slightly more complicated.

Ensure you have ovmf installed. On Gentoo, the package name is ``sys-firmware/edk2-ovmf`` or ``sys-firmware/edk2-ovmf-bin``. the latter of which is brought in by ``app-emulation/qemu`` automatically. I prefer using the non-binary version, but I had to uninstall the binary package after qemu was built. The path for locating the firmware is ``/usr/share/edk2-ovmf/OVMF_CODE.fd``, it may be different for Debian-based systems. (Currently this can be set with the ``--efi-firmware`` command line option.)

For the ``run`` and ``install`` actions, you should add the global ``--use-efi`` option:

```sh
git clone https://github.com/NucleaPeon/gentooimgr.git
python -m gentooimgr build
python -m gentooimgr --use-efi run
```

In qemu:

```sh
mkdir -p /mnt/gi
mount /dev/disk/by-label/gentooimgr /mnt/gi
cd /mnt/gi
python -m gentooimgr --use-efi --config-cloud install
python -m gentooimgr --use-efi unchroot
```

Once you have the image built, if you are adding it to proxmox, you need to:

* Set the bios to use OVMF (UEFI)
* Do **NOT** add the EFI disk as it recommends you do, since it's already a part of the image.

**Test the image using**:

``python -m gentooimgr --use-efi run [gentoo-efi-name.qcow2]``

Remove the serial options in the grub menu to get the login prompt. (Keep the ``vga`` option)



### Configurations

* ``--config-cloud`` will bring in the required components to create a cloud-init image
* ``--config-qemu`` will bring in the required components to create a qemu-enabled image, runnable in qemu or by calling ``python -m gentooimgr run [resulting-image.qcow2]``

Omitting a configuration will result in a ``base`` configuration image.

You can omit ``--config-cloud`` to create a basic gentoo image.

Using a built-in configuration flag will look in ``gentooimgr/configs/cloud.config`` for the corresponding configuration.
Writing your own configuration file and specifying an ``inherit``ed configuration will also look there if no absolute path is given.


```sh
python -m gentooimgr shrink gentoo.qcow2
```

**NOTE** Due to how ``gentooimgr`` dynamically finds the most recent portage/stage3 and iso files, if multiples exist in the same directory you may have to specify them using the appropriate flag (ie: ``--iso [path-to-iso]``). Older images can be used in this manner and eventually setting those values in the .json file should be recognized by gentooimgr so there will be no need to specify them on the command line.


## Extended Usage

GentooImgr is flexible in that it can be run on a live running system as well as on a livecd in qemu;

It's possible to automate a new bare-metal Gentoo installation (with some further development) simply by running the ``install`` action or equivalent command to install and set up everything.

Eventually, GentooImgr will be used to build gentoo turnkey OS images automatically.

----

One of the conveniences of this software is that it allows you to continue off where an error last occured.
For example, if there's an issue where a package was renamed and the compile software step fails, you can edit
the package list and rerun ``python -m gentooimgr cloud-cfg`` without any arguments and it will resume the compile
step (albeit at the beginning of that step.)

There are also commands that allow you to quickly enter the livecd chroot or run commands in the chroot:

```sh
python -m gentooimgr chroot
```

Mounts/binds are handled automatically when you chroot, but you will need to ``unchroot`` after to unmount the file systems. This is because automating unmounts right after chroot exit hasn't worked correctly (needs investigation), but an explicit unmount in an interactive shell does work as expected. Some errors may be outputted/logged, but they are not fatal.

```sh
python -m gentooimgr chroot
# do stuff
exit
python -m gentooimgr unchroot
```

## Encountered Issues

During my testing and development of this project, I found a couple notable concerns.

* Occassionally cmake fails to build. Not sure why this is, could be caused by the next issue I foundnetworkmanager
* Autoconf-wrapper was failing to emerge due to file collisions. I had to implement an ``-I /usr -I /etc`` option to get the build past the ``emerge @world`` step. My guess is autoconf had a new version but as a system tool, gentoo errs on the stability side of things.



## Adding Image to Proxmox

(Use the correct username and address to ssh/scp)


```sh
scp gentoo-[stamp].qcow2 root@proxmox:/tmp
ssh root@proxmox
# Set vmbr to your available bridge, it could be vmbr0 or vmbr1, etc.
qm create 1000 --name gentoo-templ --memory 2048 --net0 virtio,bridge=vmbr0
qm importdisk 1000 /tmp/gentoo-[stamp].qcow2 local -format qcow2
qm set 1000 --scsihw virtio-scsi-pci --scsi0 /var/lib/vz/images/1000/vm-1000-disk-0.qcow2
qm set 1000 --ide2 local:cloudinit --boot c --bootdisk scsi0 --serial0 socket --vga serial0
# The following statement is optional if you didn't shrink your disk image:
qm resize 1000 scsi0 +20G
qm set 1000 --ipconfig0 ip=dhcp
qm set 1000 --sshkey ~/.ssh/id_rsa.pub
qm template 1000

(Creating a template from this image requires clicking the "Regenerate Image" button or equivalent cli command,
after you set username and password)
```

If you are having issues with EFI images on Proxmox, instead of using qcow2 image, **USE RAW IMAGE SETTINGS**:

```sh
qm importdisk 1000 /tmp/gentoo-[stamp].qcow2 local -format raw
qm set 1000 --scsihw virtio-scsi-pci --scsi0 /var/lib/vz/images/1000/vm-1000-disk-0.raw
```

## Updating Kernel

Unless using the ``--kernel-dist`` install action option, you will be building a ``genkernel`` kernel by default.
The traditional ``make menuconfig`` command will bring in the ``.config`` configuration file, but any changes will be lost unless you copy your configuration to the corresponding ``/etc/kernels/kernel-config-*gentoo-x86_64`` file or use the ``--save-config`` option in genkernel calls in tandem with ``--menuconfig``.
If you plan on making your own changes to the kernel and having it built automatically, edit and save THAT file, instead of simply saving your menuconfig changes.

Run ``genkernel all`` and if using efi, ``cp /usr/src/linux/arch/x86/boot/bzImage /boot/efi/EFI/gentoo/bootx64.efi``

## Caveats

* [X] Forced use of Rust in cloud images (cloud-init dependency)

Unfortunately, using cloud-init brings in cryptography and oauthlib which pulls in rust. Any cloud images therefore are forced to use it, which is a large compilation target if rust-bin is not used. Some FOSS users, myself included, do not want rust installed on their systems and dislike how it is encroaching on so many FOSS areas.

Work may be done to see if this can be avoided, but for now consider it a requirement.


## TODO

* [ ] Have a way to brand a produced image with its config name (ie: gentoo-cloud.qcow2, gentoo-qemu.qcow2, etc.)
* [ ] Upload to ``pip``
* [ ] Do a check for /mnt/gentoo/etc/resolv.conf and if not found, auto copy it when using the ``chroot`` action so user isn't left without network access.
* [ ] EFI partition type functionality
* [ ] Hash check portage downloads on ``build``
* [ ] Abide by -y --days parameter for doing any checks for new gentoo files.
* [ ] have a way to set the iso creation to either ignore things not set in the config file, or have options to include dirs, etc.
* [ ] --skip-update-check : Do not even attempt to download new files in any capacity, simply use the latest ones found.
        We could implement a way to find by glob and filter by modified by state and simply use the latest modified file
        each and every time so we don't fail on multiple file detections

