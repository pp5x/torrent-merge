#!/usr/bin/env python3
import hashlib
import collections
import itertools

import config
from typing import OrderedDict, BinaryIO, Iterable

import bencodepy

File = collections.namedtuple("File", ["path", "size"])


class Pieces(Iterable):
    def __init__(self, pieces_buffer):
        self._buffer = pieces_buffer
        self._piece_hash_size = 20

    def __getitem__(self, index):
        start = index * self._piece_hash_size
        end = start + self._piece_hash_size
        return self._buffer[start:end]

    def __len__(self):
        return len(self._buffer) // self._piece_hash_size

    def __iter__(self):
        for i in range(len(self)):
            yield self[i]

    def compare_with(self, other_pieces):
        return map(lambda t: t[0] == t[1], zip(self, other_pieces))


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

    def piece_size(self) -> int:
        return self._info[b"piece length"]

    def info(self):
        return self._info.copy()

    def pieces(self) -> Pieces:
        pieces = self._info[b"pieces"]
        return Pieces(pieces)

    def files(self) -> Iterable[File]:
        if b"files" in self._info:
            return map(
                lambda f: File(f[b"path"].decode(), f[b"length"]),
                self._info[b"files"]
            )

        return [File(self.name(), self.size())]


def get_pieces_from_file(file: BinaryIO, piece_length: int,
                         start: int = 0) -> Pieces:
    file.seek(start)
    chunk = file.read(piece_length)
    pieces: bytes = b""

    while chunk:
        pieces += hashlib.sha1(chunk).digest()
        chunk = file.read(piece_length)

    return Pieces(pieces)


def torrent_print_metadata(torrent: Torrent):
    print(f"torrent name: {torrent.name()}")
    print(f"torrent hash: {torrent.hash().hexdigest()}")
    print(f"torrent piece length: {torrent.piece_size()}")
    print(f"torrent pieces count: {len(torrent.pieces())}")

    print(f"torrent file list:")
    for idx, f in enumerate(torrent.files()):
        print(f"  {idx}: {f.path} ({f.size})")


if __name__ == "__main__":
    with open(config.torrent_filename, "rb") as torrent:
        t = Torrent(torrent)
        assert t.piece_size() == 262144
        torrent_print_metadata(t)

        with open(config.original_file_path, "rb") as origin:
            o_pieces = get_pieces_from_file(origin, t.piece_size())

            print(f"number of pieces torrent: {len(t.pieces())}")
            print(f"number of pieces in origin: {len(o_pieces)}")

            matches = list(t.pieces().compare_with(o_pieces))
            print(f"{round(sum(matches) / len(matches) * 100, 2)} %")
            print(f"{sum(matches)} / {len(matches)}")

            with open(config.file_to_merge_path, "rb") as from_file:
                from_pieces = get_pieces_from_file(from_file, t.piece_size())
                print(f"number of pieces in file to merge: {len(from_pieces)}")

                # Display stats

                to_be_merged_map = list(
                    map(
                        lambda t: t[0] | t[1],
                        itertools.zip_longest(
                            t.pieces().compare_with(o_pieces),
                            t.pieces().compare_with(from_pieces),
                            fillvalue=False,
                        ),
                    )
                )
                print(
                    f"chunk to merge: {sum(to_be_merged_map)} / {len(to_be_merged_map)}"
                )

                # Compute merge

                merged_filepath = config.original_file_path.parent / (
                        config.original_file_path.name + "-merged"
                )
                with open(merged_filepath, "wb") as out:
                    for idx, (o_valid, f_valid) in enumerate(
                            itertools.zip_longest(
                                t.pieces().compare_with(o_pieces),
                                t.pieces().compare_with(from_pieces),
                            )
                    ):
                        origin.seek(idx * t.piece_size())
                        from_file.seek(idx * t.piece_size())
                        if f_valid and not o_valid:
                            out.write(from_file.read(t.piece_size()))
                        else:
                            out.write(origin.read(t.piece_size()))

                with open(merged_filepath, "rb") as out:

                    out_pieces = get_pieces_from_file(out, t.piece_size())

                    print(f"number of pieces torrent: {len(t.pieces())}")
                    print(f"number of pieces in out: {len(out_pieces)}")

                    matches = list(t.pieces().compare_with(out_pieces))
                    print(f"{round(sum(matches) / len(matches) * 100, 2)} %")
                    print(f"{sum(matches)} / {len(matches)}")
