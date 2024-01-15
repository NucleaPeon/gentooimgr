import os
import sys
import gentooimgr.config
import gentooimgr.qemu
import gentooimgr.common
import gentooimgr.errorcodes
from gentooimgr.logging import LOG

def run(args, config: dict) -> int:
    mounts = args.mounts
    image = config.get("imagename") or args.image
    auto_livecd = image is None and args.iso is None
    code = gentooimgr.errorcodes.SUCCESS
    if image is None:
        image, code = gentooimgr.qemu.create_image()

    # We need to package up our gentooimgr package into an iso and mount it to the running image
    # Why? basic gentoo livecd has no git and no pip installer. We want install to be simple
    # and use the same common codebase.

    # This will require a couple mount commands to function though.
    main_iso, code = gentooimgr.common.make_iso_from_dir(os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        ".."
    ))
    if code != gentooimgr.errorcodes.SUCCESS:
        sys.exit(code)

    LOG.debug(args)
    LOG.info(main_iso)

    code = gentooimgr.qemu.run_image(
        args,
        config,
        # Add our generated mount and livecd (assumed)
        mounts=[main_iso],
        livecd=auto_livecd
    )
    return code
