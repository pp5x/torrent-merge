#!/usr/bin/env python3
import hashlib
import config
from typing import OrderedDict

import bencodepy


def torrent_get_hash(torrent: OrderedDict):
    return hashlib.sha1(bencodepy.encode(torrent[b"info"])).hexdigest()


def torrent_print_metadata(torrent: OrderedDict):
    info = torrent[b"info"]
    print(f'torrent name: {info[b"name"].decode()}')
    print(f"torrent hash: {torrent_get_hash(torrent)}")
    print(f"torrent file list:")
    for idx, file in enumerate(info[b"files"]):
        print(f"  {idx}: {file[b'path'][0].decode()} ({file[b'length']})")


if __name__ == "__main__":
    with open(config.torrent_filename, "rb") as torrent:
        metainfo = bencodepy.decode(torrent.read())

        torrent_print_metadata(metainfo)

        config.torrent_file_to_merge_idx
