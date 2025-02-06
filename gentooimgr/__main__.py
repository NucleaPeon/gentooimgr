import os
import sys
import json
import argparse
import pathlib
import copy
import gentooimgr.common
import gentooimgr.config
import gentooimgr.configs
import gentooimgr.errorcodes
import gentooimgr.logging


def main(args):
    '''Gentoo Cloud Image Builder Utility'''
    import gentooimgr.config
    configjson = gentooimgr.config.determine_config(args)
    code = gentooimgr.errorcodes.SUCCESS
    LOG = gentooimgr.logging.LOG

    if args.action == "build":
        import gentooimgr.builder
        code = gentooimgr.builder.build(args, configjson)

    elif args.action == "run":
        import gentooimgr.run
        code = gentooimgr.run.run(args, configjson)

    elif args.action == "test":
        import gentooimgr.test
        code = gentooimgr.errorcodes.NOT_IMPLEMENTED

    elif args.action == "clean":
        import gentooimgr.clean
        code = gentooimgr.errorcodes.NOT_IMPLEMENTED

    elif args.action == "status":
        import gentooimgr.status
        code = gentooimgr.status.print_template(args, configjson)

    elif args.action == "install":
        import gentooimgr.install
        code = gentooimgr.install.configure(args, configjson)

    elif args.action == "command":
        import gentooimgr.command
        code = gentooimgr.command.command(configjson)

    elif args.action == "chroot":
        import gentooimgr.chroot
        code = gentooimgr.chroot.chroot(path=args.mountpoint, shell="/bin/bash")

    elif args.action == "unchroot":
        import gentooimgr.chroot
        code = gentooimgr.chroot.unchroot(path=args.mountpoint)

    elif args.action == "shrink":
        import gentooimgr.shrink
        fname, retcode = gentooimgr.shrink.shrink(args, configjson, stamp=args.stamp)
        LOG.info(f"\t:: Shrunken image at {fname}, {os.path.getsize(fname)}")
        code = gentooimgr.errorcodes.SUCCESS if retcode == 0 else gentooimgr.errorcodes.CONDITIONS_NOT_MET

    elif args.action == "kernel":
        import gentooimgr.kernel
        code = gentooimgr.kernel.build_kernel(args, configjson, inchroot=not os.path.exists("/mnt/gentoo"))

    return code

if __name__ == "__main__":
    """Gentoo Cloud Image Builder Utility"""
    parser = argparse.ArgumentParser(prog="gentooimgr", description="Gentoo Image Builder Utility")
    parser.add_argument("--debug", action="store_true", help="Enable verbose logging to stdout or file (with --logfile)")
    parser.add_argument("--logfile", nargs='?', type=pathlib.Path, default=None,
                        help="If this is set, log will write to the specified file. The default (unset) is to print to stdout")
    parser.add_argument("-c", "--config", nargs='?', type=pathlib.Path,
                        help="Path to a custom conf file")
    parser.add_argument("--config-cloud", action="store_const", const="cloud.json", dest="config",
                        help="Use cloud init configuration (qemu + cloud-init)")
    parser.add_argument("--config-qemu", action="store_const", const="qemu.json", dest="config",
                        help="Use a plain qemu configuration")
    parser.add_argument("--config-base", action="store_const", const="base.json", dest="config",
                        help="Use a minimal base Gentoo configuration")
    parser.add_argument("--config-g5-32", action="store_const", const="powerpc32.json", dest="config",
                        help="Use a 32-bit PowerPC G5-compatible qemu configuration")
    parser.add_argument("--config-g5-64", action="store_const", const="powerpc64.json", dest="config",
                        help="Use a 64-bit PowerPC G5-compatible qemu configuration")
    parser.add_argument("-y", "--days", type=int, default=gentooimgr.config.DAYS,
                        help="Number of days before the files are redownloaded")
    parser.add_argument("--use-efi", action="store_const", const="efi", dest="parttype",
                        help="Enable EFI for the resulting gentoo image partition type. If not set, is autodetected.")
    parser.add_argument("--use-mbr", action="store_const", const="mbr", dest="parttype",
                        help="Enable MBR for the resulting gentoo image partition type If not set, is autodetected.")
    # currently only pretends for install and maybe some kernel action. FIXME
    parser.add_argument("--pretend", action="store_true", help="Log commands instead of running them, no chrooting")

    parser.add_argument("--efi-firmware", nargs="?", default=gentooimgr.config.DEFAULT_GENTOO_EFI_FIRMWARE_PATH,
                        help="Path to the EFI firmware (OVMF_CODE.fd or similar)")
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
    parser.add_argument("--force-cloud", action='store_true',
                        help="Enables cloud-init configuration in the install phase, even if not using --config-cloud."
                        " Enables cloud modules, templates, yaml config and respective permissions. You are expected"
                        " to include cloud-init packages in your config.")
    parser.add_argument("--format", default="qcow2", help="Image format to generate, default qcow2")
    parser.add_argument("--portage", default=None, type=pathlib.Path, nargs='?',
                            help="Extract the specified portage package onto the filesystem")
    parser.add_argument("--stage3", default=None, type=pathlib.Path, nargs='?',
                            help="Extract the specified stage3 package onto the filesystem")
    parser.add_argument("--kernel-dir", default="/usr/src/linux",
                               help="Where kernel is specified. By default uses the active linux kernel")
    parser.add_argument("--kernel-dist", action="store_true",
                        help="Use a distribution kernel in the installation. Overrides all other kernel options.")
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
    parser_run = subparsers.add_parser('run', help="Run a Gentoo Image in QEMU")

    # Although not explicitly stated, if image is None and --iso is not defined, the gentoo
    # live cd is automatically inserted to a cdrom device so a `python -m gentooimgr run` command gives the
    # best experience in image building. It's only when user has a specific image or iso to mount that they will
    # define them themselves. (config is also checked for image, mounts, iso, etc. so those should be blank as well)
    parser_run.add_argument("--iso", default=None, type=pathlib.Path, nargs='?',
                            help="Mount the specified iso in qemu, should be reserved for live cd images")
    parser_run.add_argument("image", default=None, type=pathlib.Path, nargs="?",
                            help="Run the specified image in qemu")
    parser_run.add_argument("-m", "--mounts", nargs='+', default=[],
                            help="Path to iso files to mount into the running qemu instance")
    parser_run.add_argument("--use-live-cd", action="store_true",
                            help="Ensure that livecd iso is mounted and booted from. If there is no image or --iso specified, this is assumed.")

    parser_test = subparsers.add_parser('test', help="Test whether image is a legitamite cloud configured image")

    parser_clean = subparsers.add_parser('clean', help="Remove all downloaded files")
    # --force also applies to clean action

    parser_status = subparsers.add_parser('status', help="Review information, downloaded images and configurations")

    parser_install = subparsers.add_parser("install", help="Install Gentoo on a qemu guest. Defaults to "
                                           "--config-base with --kernel-dist if the respective --config or --kernel options are not provided.")
    parser_install.add_argument("--kernel-virtio", action="store_true", help="Include virtio support in non-dist kernels")
    parser_install.add_argument("--kernel-g5", action="store_true", help="Include all kernel config options for PowerMac G5 compatibility")
    parser_install.add_argument("--step-prompt", action="store_true", help="If enabled, requires <enter> to be pressed after each step is complete (for debugging)")
    parser_install.add_argument("-P", "--packages", nargs="*",
                                help="List of 'additional' packages to install on top of the current configured package list.")
    parser_install.add_argument("-S", "--services", nargs="*", help="Enable services; either specify the service name (ie: apache2) for "
                                "a default level or service:level (ie: sshd:boot) for other levels. "
                                "Useful if -P option specifies a package with a service to enable")
    parser_install.add_argument("-I", "--ignore-collisions", nargs="+", default=None,
                                help="Specify path to ignore collisions within. In the event that Gentoo fails to install dependencies on collision, "
                                "set this to `-I /usr -I /etc`")
    parser_chroot = subparsers.add_parser("chroot", help="Bind mounts and enter chroot with shell on guest. Unmounts binds on shell exit.")
    parser_chroot.add_argument("mountpoint", nargs='?', default=gentooimgr.config.GENTOO_MOUNT,
                               help="Point to mount and run the chroot and shell.")

    parser_unchroot = subparsers.add_parser("unchroot", help="Unmounts chroot filesystems")
    parser_unchroot.add_argument("mountpoint", nargs='?', default=gentooimgr.config.GENTOO_MOUNT,
                               help="Point to mount and run the chroot and shell")

    parser_cmd = subparsers.add_parser('command', help="Handle bind mounts and run command(s) in guest chroot, then unmount binds.")
    parser_cmd.add_argument("cmds", nargs='*',
                            help="Commands to run (quote each command if more than one word, ie: \"grep 'foo'\" \"echo foo\").")

    parser_shrink = subparsers.add_parser('shrink', help="Take a finalized Gentoo image and rearrange it for smaller size.")
    parser_shrink.add_argument("image", type=pathlib.Path, help="Image to shrink.")
    parser_shrink.add_argument("--stamp", nargs='?', default=None,
                               help="By default a timestamp will be added to the image name, otherwise provide "
                               "a hardcoded string to add to the image name. Result: gentoo-[stamp].img.")
    parser_shrink.add_argument("--convert", action="store_true",
                               help="For EFI images, it will error when compressing. Use --convert to enable conversion from raw"
                               " to qcow2 and then it will compress the result.")
    parser_shrink.add_argument("--only-convert", action="store_true",
                               help="Convert and exit, do not attempt to shrink the image.")
    parser_kernel = subparsers.add_parser('kernel', help="Build the kernel based on configuration and optional --kernel-dist flag.")


    args = parser.parse_args()
    gentooimgr.logging.set_logger(args)  # Pulls out logging parameters to configure logging for any process.
    gentooimgr.logging.LOG.info(f"Running {args.action} action")

    isos = gentooimgr.common.find_iso(args.download_dir)
    if args.action == "run" and args.iso is None and len(isos) > 1:
        gentooimgr.logging.LOG.error(
            f"Error: multiple iso files were found in {args.download_dir}, "
            "please specify one using `--iso [iso]` or set it in your configuration"
        )
        sys.exit(gentooimgr.errorcodes.CONDITIONS_NOT_MET)


    sys.exit(main(args))
