#!/usr/bin/env python3
import hashlib
import pprint

import config
from typing import OrderedDict

import bencodepy


def torrent_get_hash(torrent: OrderedDict):
    return hashlib.sha1(bencodepy.encode(torrent[b"info"])).hexdigest()


def torrent_print_metadata(torrent: OrderedDict):
    info = torrent[b"info"]
    print(f'torrent name: {info[b"name"].decode()}')
    print(f"torrent hash: {torrent_get_hash(torrent)}")
    print(f"torrent piece length: {info[b'piece length']}")
    print(f"torrent file list:")
    for idx, file in enumerate(info[b"files"]):
        print(f"  {idx}: {file[b'path'][0].decode()} ({file[b'length']})")

    print(info[b"pieces"][0:20])


if __name__ == "__main__":
    with open(config.torrent_filename, "rb") as torrent:
        metainfo = bencodepy.decode(torrent.read())

        torrent_print_metadata(metainfo)

        with open(config.original_file_path, "rb") as origin:
            assert (
                metainfo[b"info"][b"piece length"]
                - metainfo[b"info"][b"files"][0][b"length"]
                == 1047898
            )
            origin.seek(
                metainfo[b"info"][b"piece length"]
                - metainfo[b"info"][b"files"][0][b"length"]
            )
            hash = hashlib.sha1(
                origin.read(metainfo[b"info"][b"piece length"])
            ).digest()

            piece_sha1 = metainfo[b"info"][b"pieces"][20:40]

            if hash == piece_sha1:
                print("yes")
