GentooImgr: Gentoo Image Builder for Cloud and Turnkey ISO installers
=====================================================================

GentooImgr is a python script system to build cloud images based on Gentoo Linux.

Huge thanks to https://github.com/travisghansen/gentoo-cloud-image-builder for providing a foundation to work from.


**Features:**

* This project enables easy access to building ``systemd`` or ``openrc`` -based images.
* Performs automatic download AND verification of the linux iso, stage3 tarball and portage.
* Caches the iso and stage3 .txt files for at most a day before redownloading and rechecking for new files
* Sane and readable cli commands to build, run and test.
* Step system to enable user to continue off at the same place if a step fails
* No heavy packages like rust included ** TODO

**rename to gentooimgr, upload to pip**

Preface
-------

This project was created so I could spawn off Gentoo OS templates on my Proxmox server for various services while being more efficient than many other Linux OS's and avoiding systemd.

This python module contains all the software needed to download resources, build the image, run the image in qemu, and allow for some extensibility. The built-in functionality includes a base standard gentoo image configuration as well as a cloud-init image that can be run. You can copy the .json config file and optionally a kernel .config file to configure your image to your liking and pass it in with ``--config``.

This software is in beta so please report any issues or feature requests. You are **highly** encouraged to do so.

Thanks!

Roadmap
-------

* [X] Use gentooimgr to configure and Install a Base Gentoo OS using the least amount of configuration

    - Successfully built a gentoo qcow2 image that can be run in qemu, but it requires using the --dist-kernel flag
      as building from source still requires some work.

* [X] Use gentooimgr to create a usable cloud image (requires --dist-kernel currently)
* [ ] Use gentooimgr to create Gentoo installations on other non-amd64/non-native architectures (ex: ppc64)


Prerequisites 
-------------

* [ ] QEMU
* [ ] python3.11
* [ ] Recommended 20GB of space
* [ ] Internet Connection
* [ ] virt-sparsify (for use with `gentooimgr shrink` action)


Usage
-----

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
```

Configuring the cloud image will automatically bring in appropriate kernel configs (these are defined in ``gentooimgr/configs/cloud.config``).

Then perform any additional procedures, such as shrinking the img from 10G to ~3-4G

```sh
python -m gentooimgr shrink gentoo.qcow2
```

**NOTE** Due to how ``gentooimgr`` dynamically finds the most recent portage/stage3 and iso files, if multiples exist in the same directory you may have to specify them using the appropriate flag (ie: ``--iso [path-to-iso]``). Older images can be used in this manner and eventually setting those values in the .json file should be recognized by gentooimgr so there will be no need to specify them on the command line.



Extended Usage
--------------

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

Mounts/binds are handled automatically when you chroot, but you will need to ``unchroot`` after to unmount the file systems:

```sh
python -m gentooimgr chroot
# do stuff
exit
python -m gentooimgr unchroot
```


Adding Image to Proxmox
-----------------------

(Use the correct username and address to ssh/scp)

```sh
scp gentoo-[stamp].qcow2 root@proxmox:/tmp
ssh root@proxmox
# Set vmbr to your available bridge, it could be vmbr0 or vmbr1, etc.
qm create 1000 --name gentoo-templ --memory 2048 --net0 virtio,bridge=vmbr0
qm importdisk 1000 /tmp/gentoo-[stamp].qcow2 local -format qcow2
qm set 1000 --scsihw virtio-scsi-pci --scsi0 /var/lib/vz/images/1000/vm-1000-disk-0.qcow2
qm set 1000 --ide2 local:cloudinit --boot c --bootdisk scsi0 --serial0 socket --vga serial0
qm resize 1000 scsi0 +20G
qm set 1000 --ipconfig0 ip=dhcp
qm set 1000 --sshkey ~/.ssh/id_rsa.pub
qm template 1000

(Creating a template from this image requires clicking the "Regenerate Image" button or equivalent cli command,
after you set username and password)
```

Caveats
--------

* [X] Forced use of Rust in cloud images (cloud-init dependency)

Unfortunately, using cloud-init brings in cryptography and oauthlib which pulls in rust. Any cloud images therefore are forced to use it, which is a large compilation target if rust-bin is not used. Some FOSS users, myself included, do not want rust installed on their systems and dislike how it is encroaching on so many FOSS areas.

Work may be done to see if this can be avoided, but for now consider it a requirement.


TODO
----

* [ ] Hash check portage downloads on ``build``
* [ ] have a way to set the iso creation to either ignore things not set in the config file, or have options to include dirs, etc.
* [ ] --skip-update-check : Do not even attempt to download new files in any capacity, simply use the latest ones found.
        We could implement a way to find by glob and filter by modified by state and simply use the latest modified file
        each and every time so we don't fail on multiple file detections
