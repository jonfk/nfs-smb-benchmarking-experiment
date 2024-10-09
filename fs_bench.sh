#!/bin/bash

# Define mount points
NFS_MOUNT="/mnt/nfs/ds218/backups"
SMB_MOUNT="/mnt/smb/ds218/backups"

# Define test file size and name
FILE_SIZE="1G"
TEST_FILE="test_file"

# Function to run fio test
run_fio_test() {
    mount_point=$1
    test_name=$2
    echo "Running $test_name test on $mount_point"
    fio --name=$test_name \
        --filename=$mount_point/$TEST_FILE \
        --size=$FILE_SIZE \
        --rw=$3 \
        --bs=$4 \
        --direct=1 \
        --numjobs=4 \
        --runtime=60 \
        --group_reporting
    echo ""
}

# Run tests for each mount point
for MOUNT in "$NFS_MOUNT" "$SMB_MOUNT"; do
    echo "Testing $MOUNT"

    # Sequential read
    run_fio_test $MOUNT "sequential_read" "read" "1M"

    # Sequential write
    run_fio_test $MOUNT "sequential_write" "write" "1M"

    # Random read
    run_fio_test $MOUNT "random_read" "randread" "4k"

    # Random write
    run_fio_test $MOUNT "random_write" "randwrite" "4k"

    # Mixed random read/write
    run_fio_test $MOUNT "mixed_randrw" "randrw" "4k"

    # Clean up
    rm $MOUNT/$TEST_FILE
done
