# GentooImgr: Gentoo Image Builder for Cloud and Turnkey ISO installers


GentooImgr is a python script system to automatically build gentoo, specifically qemu and cloud images, or for a native installation.

It will download portage and stage3 archives, handle mounting, chrooting and other aspects. The aim of this project is to enable users to obtain a base gentoo installation for various scenarios, ideally, in one command. Common use cases and their useful options will be detailed below.

GentooImgr separates all the typical areas from the Gentoo Handbook into ``steps`` which can be called individually or collectively with an ``install``.

Huge thanks to https://github.com/travisghansen/gentoo-cloud-image-builder for providing a foundation to work from.


**Features:**

* This project enables easy access to building ``systemd`` or ``openrc`` -based images.
* Performs automatic download AND verification of the linux iso, stage3 tarball and portage.
* Caches the iso and stage3 .txt files for at most a day before redownloading and rechecking for new files
* Sane and readable cli commands to build, run and test.
* Step system to enable user to continue off at the same place if a step fails
* No heavy packages like rust included ** Cloud Init images do require rust, QEMU-only doesn't. (TODO)

**IMPORTANT**: Gentoo with EFI and Cloud-Init configuration is buggy: https://github.com/canonical/cloud-init/issues/3999, it is not recommended at the moment.

## Common Usage

### Basic QEMU Build:

QEMU builds a virtual image file that can be run in a virtualized environment


```sh
git clone https://github.com/NucleaPeon/gentooimgr.git
python -m gentooimgr build
python -m gentooimgr run
```

Once the image is virtualized, within qemu mount the available gentooimgr iso and run the appropriate command:

```sh
mkdir -p /mnt/gi
mount /dev/disk/by-label/gentooimgr /mnt/gi
cd /mnt/gi
python -m gentooimgr install
python -m gentooimgr unchroot
```

...

### Cloud-Image Build:

Complete the Basic QEMU Build but tkae the install action command and add the ``--config-cloud`` option. (This is a built-in configuration)

```sh
python -m gentooimgr --config-cloud install

```

Cloud-Image configures a qemu image that can be imported into network/kvm/hosting applications with direct ability to configure things such as hardware (network), passwords, ssh keys and more, sometimes without rebooting and makes administration outside of the virtualized environment very easy.

...

### PowerMac G5 Native Install:

Important to note that the Gentoo minimal ppc cd does not include setuptools or pip, so I've included ``pyvenvex.py``, a very useful script that will download setuptools and pip for a virtual environment that gentooimgr can be installed into.

(change ``-config-ppc-64`` to ``--config-ppc-32`` if you prefer a 32-bit configuration)

Load up the minimal iso image and run:

```sh
cd /root
git clone https://github.com/NucleaPeon/gentooimgr.git
cd /root/gentooimgr
python pyvenvex.py .
bin/pip install -r requirements.txt -e .
bin/python -m gentooimgr -N -I --config-ppc-64 install
# Or use --config-ppc-32
```

PPC ignores the ``--use-efi``flag, as OpenFirmware already uses EFI and there's very little room to customize new world mac boot processes due to how particular they are.

__NOTE__: Gentoo is currently having issues with ``genkernel`` and ``apmd``/``powermgmt-base`` packages that prevent this from being a single-command success for emerging packages. ``acpid`` requires an ``ACCEPT_KEYWORDS="**"`` env var or /etc/portage/package.accept_keywords/ entry to overcome this. I will be temporarily removing power management from the process.

* genkernel: https://bugs.gentoo.org/show_bug.cgi?id=955278
* powermgmt-base: https://bugs.gentoo.org/show_bug.cgi?id=955437


## Preface

This project was created so I could spawn off Gentoo OS templates on my Proxmox server for various services while being more efficient than many other Linux OS's and avoiding systemd.

This python module contains all the software needed to download resources, build the image, run the image in qemu, and allow for some extensibility. The built-in functionality includes a base standard gentoo image configuration as well as a cloud-init image that can be run. You can copy the .json config file and optionally a kernel .config file to configure your image to your liking and pass it in with ``--config``.

This software is in beta so please report any issues or feature requests. You are **highly** encouraged to do so.

Thanks!

## Roadmap

* [X] Use gentooimgr to configure and Install a Base Gentoo OS using the least amount of configuration
* [X] Use gentooimgr to create a usable cloud image without a binary dist kernel
* [X] Use gentooimgr to create Gentoo installations on other non-amd64/non-native architectures (ex: ppc64, arm)
* [ ] Gentoo ARM doesn't have an iso available to download, so I will be producing one.
* [ ] Allow better handling from image building third party software such as ansible and terraform
* [ ] Build turnkey (LXC) images
* [ ] Fix step invocation to a nicer implementation. Currently in install.py, these should be their own classes and dynamically loaded in based on architecture (with default/base fallbacks) so users can simply drop in a folder of class definitions to customize an architecture's build and install process.

## Prerequisites

* [ ] QEMU
* [ ] python3.11 and pip (to install deps)
* [ ] Recommended 20GB of space
* [ ] Internet Connection
* [ ] virt-sparsify (for use with `gentooimgr shrink` action, optional, found in ``app-emulation/guestfs-tools`` package)
* [ ] OVMF firmware for using EFI enabled images (optional)
* [ ] progressbar for python (dev-python/progressbar2 package if running on gentoo)


## Using EFI

Ensure you have ``ovmf`` installed. On Gentoo, the package name is ``sys-firmware/edk2-ovmf`` or ``sys-firmware/edk2-ovmf-bin``. the latter of which is brought in by ``app-emulation/qemu`` automatically. I prefer using the non-binary version, but I had to uninstall the binary package after qemu was built. The path for locating the firmware is ``/usr/share/edk2-ovmf/OVMF_CODE.fd``, it may be different for Debian-based systems. (Currently this can be set with the ``--efi-firmware`` command line option.)

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



## Configurations

* ``--config-cloud`` will bring in the required components to create a cloud-init image
* ``--config-qemu`` will bring in the required components to create a qemu-enabled image, runnable in qemu or by calling ``python -m gentooimgr run [resulting-image.qcow2]``
* ``--config-ppc-64`` will build and install a PowerPC G5 sustem but must be run from the livecd. Use ``-N`` and ``-I`` (new world mac and install-only options)

Omitting a configuration flag will result in a ``base`` configuration image being built.

Using a built-in configuration flag will look in ``gentooimgr/configs/`` for the corresponding configuration.
Writing your own configuration file and specifying an ``inherit``ed configuration will also look there for the inherited file if no absolute path is given.


```sh
python -m gentooimgr shrink gentoo.qcow2
```

## Caveats

* [ ] Due to how ``gentooimgr`` dynamically finds the most recent portage/stage3 and iso files, if multiples exist in the same directory you may have to specify them using the appropriate flag (ie: ``--iso [path-to-iso]``) or put the specific file in your config. Another way to ensure things are up to date and require no intervention is to run ``python -m gentooimgr clean`` before your build/run/install steps.

* [X] Forced use of Rust in cloud images (cloud-init dependency)

Unfortunately, using cloud-init brings in cryptography and oauthlib which pulls in rust. Any cloud images therefore are forced to use it, which is a large compilation target if rust-bin is not used. Some FOSS users, myself included, do not want rust installed on their systems and dislike how it is encroaching on so many FOSS areas.

Work may be done to see if this can be avoided, but for now consider it a requirement.




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

## Encountered Issues / Troubleshooting

During my testing and development of this project, I found a couple notable concerns.

* Occassionally cmake fails to build. Not sure why this is, could be caused by the next issue I found:
* Autoconf-wrapper was failing to emerge due to file collisions. I had to implement an ``-I /usr -I /etc`` option to get the build past the ``emerge @world`` step. My guess is autoconf had a new version but as a system tool, gentoo errs on the stability side of things.

* Since dev-build/cmake package name was updated, I did encounter another issue while compiling cmake. It was along the lines of:

```
fatal error killed signal terminated program cc1plus 
cmBuildCommand.o Error 1
```

A quick search seems to indicate that running a compile job with too many threads can increase memory to the point where there is an out of memory error, or something. We default to max # of threads, my system has 32. The ``run`` action has a command line flag ``--memory``/``-M`` that can be used to increase memory and resolve this problem.
My system was set to vie gentooimgr 16GB of RAM and it compiled without error.



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
qm importdisk 1000 /tmp/gentoo[-timestamp].qcow2 local -format raw
qm set 1000 --scsihw virtio-scsi-pci --scsi0 /var/lib/vz/images/1000/vm-1000-disk-0.raw
```

## Updating Kernel

Unless using the ``--kernel-dist`` install action option, you will be building a ``genkernel`` kernel if 'genkernel' is found in your kernel packages. Otherwise it will build a ``gentoo-sources`` kernel. No downloading and configuring a kernel.org kernel yet.

**(Building with kernel source is planned but not yet available)**

## TODO

* [ ] We already use max threads when compiling. Check total memory and allocate a more considerate amount if available. ie: 16GB of RAM should allow up to 8GB to qemu. No more than 50% unless explicitly set.
* [ ] Have a way to include custom make.conf in install process. (its own step?)
* [ ] Have a way to brand a produced image with its config name (ie: gentoo-cloud.qcow2, gentoo-qemu.qcow2, etc.)
* [ ] Upload this code to ``pip``
* [ ] Kernel source compilation during install phase. Potentially download during build phase.
* [ ] Do a check for /mnt/gentoo/etc/resolv.conf and if not found, auto copy it when using the ``chroot`` action so user isn't left without network access.
* [ ] EFI partition type functionality
* [ ] Hash check portage downloads on ``build``
* [ ] Abide by -y --days parameter for doing any checks for new gentoo files.
* [ ] have a way to set the iso creation to either ignore things not set in the config file, or have options to include dirs, etc.
* [ ] --skip-update-check : Do not even attempt to download new files in any capacity, simply use the latest ones found.
        We could implement a way to find by glob and filter by modified by state and simply use the latest modified file
        each and every time so we don't fail on multiple file detections

