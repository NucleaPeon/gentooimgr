GenCloud: Gentoo Cloud Image Builder
====================================

GenCloud is a python script system to build cloud images based on Gentoo Linux.

**Features:**

* This project enables easy access to building ``systemd`` or ``openrc`` -based images.
* Performs automatic download AND verification of the linux iso, stage3 tarball and portage.
* Caches the iso and stage3 .txt files for at most a day before redownloading and rechecking for new files
* Sane and readable cli commands to build, run and test.


Usage
-----

```sh
git clone https://github.com/NucleaPeon/gencloud.git
python -m gencloud build
python -m gencloud run
```

Once qemu is running, mount the available gencloud iso and run the appropriate command:

```sh
mkdir -p /mnt/gencloud
mount /dev/disk/by-label/gencloud /mnt/gencloud
cd /mnt/gencloud
python -m gencloud cloud-cfg --virtio
```


