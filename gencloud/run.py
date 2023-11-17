import os
import gencloud.config
import gencloud.qemu
import gencloud.common

def run(args, image: str = gencloud.config.GENTOO_IMG_NAME):
    isos = gencloud.common.find_iso(args.download_dir)
    if len(isos) == 1:
        # We need to package up our gencloud package into an iso and mount it to the running image
        # Why? basic gentoo livecd has no git and no pip installer. We want install to be simple
        # and use the same common codebase.
        # This will require a couple mount commands to function though.
        iso = gencloud.common.make_iso_from_dir(os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            ".."
        ))
        mounts = []
        if iso:
            mounts = [iso]

        for m in args.mounts:
            if os.path.exists(m):
                mounts.append(m)

        print(f"\t:: Mounts: {isos[0]}")
        gencloud.qemu.run_image(isos[0], image=image, mount_isos=mounts)

    else:
        print("More than one iso image was found.\nPlease run `python -m gencloud run --iso [iso]`")


