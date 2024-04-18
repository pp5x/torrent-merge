#!/usr/bin/env python3
import hashlib
import collections

import config
from typing import OrderedDict, BinaryIO, Iterable

import bencodepy

File = collections.namedtuple("File", ["path", "size"])


class Pieces(object):
    def __init__(self, pieces_buffer):
        self._buffer = pieces_buffer
        self._piece_hash_size = 20

    def __getitem__(self, index):
        start = index * self._piece_hash_size
        end = start + self._piece_hash_size
        return self._buffer[start:end]


class Torrent(object):

    def __init__(self, file: BinaryIO):
        self._data = bencodepy.decode(file.read())
        self._info: OrderedDict = self._data[b"info"]

    def hash(self):
        return hashlib.sha1(bencodepy.encode(self._info))

    def name(self) -> str:
        return self._info[b"name"].decode()

    def size(self) -> int:
        return self._info[b"length"]

    def piece_length(self) -> int:
        return self._info[b"piece length"]

    def info(self):
        return self._info.copy()

    def pieces(self) -> Pieces:
        pieces = self._info[b"pieces"]
        return Pieces(pieces)

    def files(self) -> Iterable[File]:
        if b"files" in self._info:
            return map(
                lambda f: File(f[b"path"].decode(), f[b"length"]), self._info[b"files"]
            )

        return [File(self.name(), self.size())]


def torrent_print_metadata(torrent: Torrent):
    print(f"torrent name: {torrent.name()}")
    print(f"torrent hash: {torrent.hash().hexdigest()}")
    print(f"torrent piece length: {torrent.piece_length()}")

    print(f"torrent file list:")
    for idx, f in enumerate(torrent.files()):
        print(f"  {idx}: {f.path} ({f.size})")


if __name__ == "__main__":
    with open(config.torrent_filename, "rb") as torrent:
        t = Torrent(torrent)
        torrent_print_metadata(t)

        with open(config.original_file_path, "rb") as origin:
            assert t.piece_length() == 262144
            origin.seek(0)

            hash = hashlib.sha1(origin.read(t.piece_length())).digest()
            piece_sha1 = t.pieces()[0]

            assert len(hash) == len(piece_sha1)

            print(f"piece hash: {hash}")
            print(f"expected hash: {piece_sha1}")

            if hash == piece_sha1:
                print("yes")
