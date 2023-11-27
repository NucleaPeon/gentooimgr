import os
import gentooimgr.config
import gentooimgr.qemu
import gentooimgr.common

def run(args):
    mounts = args.mounts
    # Specified image or look for gentoo.{img,qcow2}
    image = args.image or gentooimgr.qemu.create_image()
    # We need to package up our gentooimgr package into an iso and mount it to the running image
    # Why? basic gentoo livecd has no git and no pip installer. We want install to be simple
    # and use the same common codebase.
    # This will require a couple mount commands to function though.
    main_iso = gentooimgr.common.make_iso_from_dir(os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        ".."
    ))

    print("Before run_image")
    gentooimgr.qemu.run_image(
        args,
        iso=args.iso,
        # Add our generated mount and livecd (assumed)
        mounts=[main_iso]
    )
