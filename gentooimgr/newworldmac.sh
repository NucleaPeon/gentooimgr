#!/bin/sh
#
# $1: disk to partition, ie: /dev/sda
# $2: size (empty, or <enter> to use full disk)
#
# This creates a hard drive with an Apple partition map
# and the following partitions:
#
#   bootstrap of 800k
#   ext2 linux boot partition of 512M
#   swap of max 16G (max ram in a G5 PowerMac) FIXME: able to specify and/or set to total memory installed
#   rootfs of the rest of drive
#


prog='mac-fdisk'
haspart=`$prog -l`
IFS='
'

if [[ $haspart == *"$1"* ]]; then
    echo "$1 has a partition map"
    cat <<EOF | $prog $1
i
y
$IFS
w
y
b
64
c
512M
boot
1664
16G
Swap
c
33556096
16G
w
y
q
EOF


else
    cat <<EOF | $prog $1
i
w
y
b
64
c
512M
boot
1664
16G
Swap
c
33556096
16G
w
y
q
EOF

fi
#
# # Get start of last partition +1
# last_sector=`parted /dev/sda 'unit s print' | tail -n2 | awk '$1 ~ /[0-9]+/ { print $3 }' | grep -o '[0-9]\+'`
# echo $last_sector
# last_sector=$last_sector+1
# echo "$last_sector +1"
# cat <<EOF | parted /dev/sda
# mkpart
# rootfs
# ext4
# $last_sector
# 100%
# EOF
