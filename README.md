GentooImgr: Gentoo Image Builder for Cloud and Turnkey ISO installers
=====================================================================

GentooImgr is a python script system to build cloud images based on Gentoo Linux.

**Features:**

* This project enables easy access to building ``systemd`` or ``openrc`` -based images.
* Performs automatic download AND verification of the linux iso, stage3 tarball and portage.
* Caches the iso and stage3 .txt files for at most a day before redownloading and rechecking for new files
* Sane and readable cli commands to build, run and test.
* Step system to enable user to continue off at the same place if a step fails
* No heavy packages like rust included ** TODO

**rename to gentooimgr, upload to pip**

Usage
-----

```sh
git clone https://github.com/NucleaPeon/gentooimgr.git
python -m gentooimgr build
python -m gentooimgr run
```

Once qemu is running, mount the available gentooimgr iso and run the appropriate command:

```sh
mkdir -p /mnt/gentooimgr
mount /dev/disk/by-label/gentooimgr /mnt/gentooimgr
cd /mnt/gentooimgr
python -m gentooimgr cloud-cfg --virtio
```

Perform any additional procedures, such as shrinking the img from 10G to ~3-4G

```sh
python -m gentooimgr shrink gentoo.qcow2
```


Extended Usage
--------------

GentooImgr is flexible in that it can be run on a live running system as well as on a livecd in qemu;

It's possible to automate a new bare-metal Gentoo installation (with some further development) simply by running ``cloud-cfg`` or equivalent command to install and set up everything.

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

Mounts/binds are handled automatically when you exit the chroot.

```sh
python -m gentooimgr command "ls /mnt/gentoo"
```

The above will fail because the command is run in the chroot which doesn't have an ``/mnt/gentoo`` directory in it. Multiple commands can be given, simply list each one in quotes: ``python -m gentooimgr command "/bin/cmd 1" "/bin/cmd 2" "/bin/cmd 3 foo bar"``.


Adding Image to Proxmox
-----------------------

(Use the correct username and address to ssh/scp)

```sh
scp gentoo-[stamp].qcow2 root@proxmox:/tmp
ssh root@proxmox
qm create 1000 --name gentoo-templ --memory 2048 --net0 virtio,bridge=vmbr1
qm importdisk 1000 /tmp/gentoo-[stamp].qcow2 local -format qcow2
qm set 1000 --scsihw virtio-scsi-pci --scsi0 /var/lib/vz/images/9000/vm-1000-disk-0.qcow2
qm set 1000 --ide2 local:cloudinit --boot c --bootdisk scsi0 --serial0 socket --vga serial0
qm resize 1000 scsi0 +20G
qm set 1000 --ipconfig0 ip=dhcp
qm set 1000 --sshkey ~/.ssh/id_rsa.pub
qm template 1000
```


TODO
----

* [ ] Hash check portage downloads on ``build``
* [ ] --skip-update-check : Do not even attempt to download new files in any capacity, simply use the latest ones found.
        We could implement a way to find by glob and filter by modified by state and simply use the latest modified file
        each and every time so we don't fail on multiple file detections
