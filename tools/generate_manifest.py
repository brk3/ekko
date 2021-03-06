#!/usr/bin/env python

# Copyright 2016 Sam Yaple
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Copied and licensed from https://github.com/SamYaple/osdk


import argparse
import os
import sys

from ekko.manifest import structure as manifest_structure
from six.moves import range
from stevedore import driver


def parse_args():
    parser = argparse.ArgumentParser(description='Backup Block Device')
    parser.add_argument('--backupsize', required=True, type=int,
                        help='Size of backup for manifest gen (size in GB)')
    parser.add_argument('--manifest', required=True,
                        help='manifest file')
    parser.add_argument('--cbt', required=False,
                        help='change block tracking info')
    parser.add_argument('--driver', required=False, default='sqlite',
                        choices=['osdk', 'sqlite'], help='manifest driver')
    return parser.parse_args()


def read_segments(segments, metadata):
    for segment in segments:
        yield manifest_structure.Segment(
            metadata.backupset_id,
            metadata.incremental,
            segment,
            0,
            0,
            os.urandom(20)
        )


def check_manifest(manifest_file):
    return os.path.isfile(manifest_file)


def main():
    args = parse_args()
    if check_manifest(args.manifest):
        print('manifest exists; exiting')
        return

    manifest = driver.DriverManager(
        namespace='ekko.manifest.drivers',
        name=args.driver,
        invoke_on_load=True,
        invoke_args=[args.manifest]
    ).driver

    size_of_disk = args.backupsize * 1024**3  # Convert GB to B
    incremental = 0
    metadata = manifest_structure.Metadata(incremental, size_of_disk)

    manifest.initialize()
    manifest.put_metadata(metadata)

    num_of_segments = int(size_of_disk / metadata.segment_size)
    segments = read_segments(range(0, num_of_segments - 1), metadata)

    manifest.put_segments(segments, metadata)

if __name__ == '__main__':
    sys.exit(main())
