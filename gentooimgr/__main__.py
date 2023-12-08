import os
import sys
import json
import argparse
import pathlib
import copy
import gentooimgr.common
import gentooimgr.config
import gentooimgr.configs


def main(args):
    '''Gentoo Cloud Image Builder Utility'''
    import gentooimgr.config
    configjson = gentooimgr.config.determine_config(args)

    if args.action == "build":
        import gentooimgr.builder
        gentooimgr.builder.build(args, configjson)

    elif args.action == "run":
        import gentooimgr.run
        gentooimgr.run.run(args, configjson)

    elif args.action == "test":
        import gentooimgr.test

    elif args.action == "clean":
        import gentooimgr.clean

    elif args.action == "status":
        import gentooimgr.status
        gentooimgr.status.print_template(args, configjson)

    elif args.action == "install":
        import gentooimgr.install
        gentooimgr.install.configure(args, configjson)

    elif args.action == "command":
        import gentooimgr.command
        gentooimgr.command.command(configjson)

    elif args.action == "chroot":
        import gentooimgr.chroot
        gentooimgr.chroot.chroot(path=args.mountpoint, shell="/bin/bash")

    elif args.action == "shrink":
        import gentooimgr.shrink
        fname = gentooimgr.shrink.shrink(args, config, stamp=args.stamp)
        print(f"Shrunken image at {fname}, {os.path.getsize(fname)}")

    elif args.action == "kernel":
        import gentooimgr.kernel
        specs = [
            args.virtio
        ]
        specs = [ s for s in specs if s ]  # remove invalid values
        gentooimgr.kernel.kernel_conf_apply(args.kernel_dir, specs)

if __name__ == "__main__":
    """Gentoo Cloud Image Builder Utility"""
    parser = argparse.ArgumentParser(prog="gentooimgr", description="Gentoo Image Builder Utility")
    parser.add_argument("-c", "--config", nargs='?', type=pathlib.Path,
                        help="Path to a custom conf file")
    parser.add_argument("--config-cloud", action="store_const", const="cloud.json", dest="config",
                        help="Use cloud init configuration")
    parser.add_argument("--config-base", action="store_const", const="base.json", dest="config",
                        help="Use a minimal base Gentoo configuration")

    parser.add_argument("-t", "--temporary-dir", nargs='?', type=pathlib.Path,
                        default=os.getcwd(), help="Path to temporary directory for downloading files")
    parser.add_argument("-j", "--threads", type=int, default=gentooimgr.config.THREADS,
                        help="Number of threads to use for building and emerging software")
    parser.add_argument("-d", "--download-dir", type=pathlib.Path, default=os.getcwd(),
                        help="Path to the desired download directory (default: current)")
    parser.add_argument("--openrc", dest="profile", action="store_const", const="openrc",
                        help="Select OpenRC as the Gentoo Init System")
    parser.add_argument("--systemd", dest="profile", action="store_const", const="systemd",
                        help="Select SystemD as the Gentoo Init System")
    parser.add_argument("-f", "--force", action="store_true",
                        help="Let action occur at potential expense of data loss or errors (applies to clean and cloud-cfg)")
    parser.add_argument("--format", default="qcow2", help="Image format to generate, default qcow2")
    parser.add_argument("--portage", default=None, type=pathlib.Path, nargs='?',
                            help="Extract the specified portage package onto the filesystem")
    parser.add_argument("--stage3", default=None, type=pathlib.Path, nargs='?',
                            help="Extract the specified stage3 package onto the filesystem")
    parser.add_argument("--virtio", action="store_const", const="virtio",
                              help="Bring in virtio support")
    subparsers = parser.add_subparsers(help="gentooimgr actions", dest="action")
    subparsers.required = True

    # Build action
    parser_build = subparsers.add_parser('build', help="Download and verify all the downloaded components for cloud image")
    parser_build.add_argument("image", default=gentooimgr.config.GENTOO_IMG_NAME, type=str, nargs='?',
                              help="Specify the exact image (date) you want to build; ex: 20231112T170154Z. Defaults to downloading the latest image. If image exists, will automatically use that one instead of checking online.")
    parser_build.add_argument("--size", default="12G", help="Size of image to build")
    parser_build.add_argument("--no-verify", dest="verify", action="store_false", help="Do not verify downloaded iso")
    parser_build.add_argument("--verify", dest="verify", action="store_true", default=True,
                              help="Verify downloaded iso")
    parser_build.add_argument("--redownload", action="store_true", help="Overwrite downloaded files")
    parser_run = subparsers.add_parser('run', help="Run a Gentoo Image in QEMU to process it into a cloud image")

    parser_run.add_argument("--iso", default=None, type=pathlib.Path, nargs='?',
                            help="Mount the specified iso in qemu, should be reserved for live cd images")
    parser_run.add_argument("image", default=gentooimgr.config.GENTOO_IMG_NAME,
                            type=pathlib.Path, nargs="?",
                            help="Run the specified image in qemu")
    parser_run.add_argument("-m", "--mounts", nargs='+', default=[],
                            help="Path to iso files to mount into the running qemu instance")

    parser_test = subparsers.add_parser('test', help="Test whether image is a legitamite cloud configured image")

    parser_clean = subparsers.add_parser('clean', help="Remove all downloaded files")
    # --force also applies to clean action

    parser_status = subparsers.add_parser('status', help="Review information, downloaded images and configurations")

    parser_install = subparsers.add_parser("install", help="Install Gentoo on a qemu guest. Defaults to "
                                           "--config-base with --kernel-dist if the respective --config or --kernel options are not provided.")
    parser_install.add_argument("--kernel-dist", action="store_true",
                              help="Use a distribution kernel in the installation. Overrides all other kernel options.")
    parser_install.add_argument("--kernel-virtio", action="store_true", help="Include virtio support in non-dist kernels")
    parser_install.add_argument("--kernel-g5", action="store_true", help="Include all kernel config options for PowerMac G5 compatibility")

    parser_chroot = subparsers.add_parser("chroot", help="Bind mounts and enter chroot with shell on guest. Unmounts binds on shell exit")
    parser_chroot.add_argument("mountpoint", nargs='?', default=gentooimgr.config.GENTOO_MOUNT,
                               help="Point to mount and run the chroot and shell")

    parser_cmd = subparsers.add_parser('command', help="Handle bind mounts and run command(s) in guest chroot, then unmount binds")
    parser_cmd.add_argument("cmds", nargs='*',
                            help="Commands to run (quote each command if more than one word, ie: \"grep 'foo'\" \"echo foo\")")

    parser_shrink = subparsers.add_parser('shrink', help="Take a finalized Gentoo image and rearrange it for smaller size")
    parser_shrink.add_argument("img", type=pathlib.Path, help="Image to shrink")
    parser_shrink.add_argument("--stamp", nargs='?', default=None,
                               help="By default a timestamp will be added to the image name, otherwise provide "
                               "a hardcoded string to add to the image name. Result: gentoo-[stamp].img")

    parser_kernel = subparsers.add_parser('kernel', help="Explicitly set up just the kernel config")
    parser_kernel.add_argument("--kernel-dir", default="/usr/src/linux",
                               help="Where kernel is specified. By default uses the active linux kernel")


    args = parser.parse_args()

    isos = gentooimgr.common.find_iso(args.download_dir)
    if args.action == "run" and args.iso is None and len(isos) > 1:
        print(f"Error: multiple iso files were found in {args.download_dir}, please specify one using `--iso [iso]`")
        sys.exit(1)


    main(args)
