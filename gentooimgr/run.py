import os
import sys
import gentooimgr.config
import gentooimgr.qemu
import gentooimgr.common
import gentooimgr.errorcodes
from gentooimgr.logging import LOG

def run(args, config: dict, **kwargs) -> int:
    print(args, config)
    mounts = args.mounts
    c = gentooimgr.config.config(architecture=config.get("architecture", "amd64"))
    image = config.get("imagename") or args.image
    auto_livecd = image is None and args.iso is None or args.use_live_cd
    code = gentooimgr.errorcodes.SUCCESS
    qemu_prog = c.GENTOO_CMD
    if image is None:
        image, code = gentooimgr.qemu.create_image(args, config, args.force)

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
