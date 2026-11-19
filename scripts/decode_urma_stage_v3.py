#!/usr/bin/env python3
"""Decode a URMA stage-buffer V3 file (reader side) and print an aggregate table.

File format (see include/spdk_internal/urma_stage_buffer.h):
  header: magic[8]="URMA3B01", 8 x uint64 (version, side, record_bytes,
          capacity, attempted, count, dropped, mode)  -> 72 bytes
  records: count x record_bytes (192 = 24 x uint64, little endian)
  footer: magic[8]="URMA3END", uint64 count, uint64 dropped -> 24 bytes

Reader record layout (lib/nvme/nvme_urma.c, V3 append):
  [0]  trace_seq            [1]  qid
  [2]  cid                  [3]  opcode
  [4]  lba                  [5]  blocks
  [6]  initiator_ticks_hz   [7]  submit_tick
  [8]  send_start           [9]  release_start_tick
  [10] release_end_tick     [11] complete_tick
  [12] completion_mono_ns   [13] target stage flags
  [14] target_lcore         [15] target_ticks_hz
  [16] target_rx_tick       [17] target_buffer_tick
  [18] target_exec_tick     [19] target_bdev_cpl_tick
  [20] target_data_post_tick[21] target_data_cpl_tick
  [22] target_trace_seq     [23] reserved

Only stdlib is used; records are streamed in chunks and reduced into
histograms so multi-GB files can be decoded on a small machine.
"""

import argparse
import os
import struct
import sys

HEADER = struct.Struct("<8s8Q")
FOOTER = struct.Struct("<8sQQ")
RECORD_BYTES = 192
FIELDS = 24
REC = struct.Struct("<24Q")

METRICS = [
    # name, kind: "all" = every record, "valid" = records with a complete target stage
    ("roundtrip_us", "all"),
    ("pre_send_us", "all"),
    ("release_us", "all"),
    ("target_us", "valid"),
    ("rx_buffer_us", "valid"),
    ("buffer_exec_us", "valid"),
    ("bdev_us", "valid"),
    ("bdev_post_us", "valid"),
    ("data_us", "valid"),
    ("residual_us", "valid"),
    ("outside_us", "valid"),
]
BIN_US = 1
MAX_BIN_US = 200000  # 200 ms; larger values go to one overflow bin


def ticks_to_us(ticks, hz):
    if hz == 0:
        return 0
    return ticks // hz * 1000000 + (ticks % hz) * 1000000 // hz


def new_hist():
    return {"bins": [0] * (MAX_BIN_US // BIN_US + 1), "over": 0, "n": 0,
            "sum": 0, "mn": None, "mx": 0}


def add(hist, value):
    hist["n"] += 1
    hist["sum"] += value
    if hist["mn"] is None or value < hist["mn"]:
        hist["mn"] = value
    if value > hist["mx"]:
        hist["mx"] = value
    idx = value // BIN_US
    if idx >= len(hist["bins"]):
        hist["over"] += 1
    else:
        hist["bins"][idx] += 1


def percentile(hist, p):
    if hist["n"] == 0:
        return 0
    target = int(hist["n"] * p)
    if target >= hist["n"]:
        target = hist["n"] - 1
    seen = 0
    for i, c in enumerate(hist["bins"]):
        seen += c
        if seen > target:
            return i * BIN_US
    return MAX_BIN_US


def read_exact(f, n):
    data = f.read(n)
    if len(data) != n:
        raise IOError("short read: wanted %d, got %d" % (n, len(data)))
    return data


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--out", default=None)
    ap.add_argument("--max-records", type=int, default=0)
    args = ap.parse_args()

    size = os.path.getsize(args.path)
    with open(args.path, "rb") as f:
        raw = read_exact(f, HEADER.size)
        magic, version, side, record_bytes, capacity, attempted, count, dropped, mode = \
            HEADER.unpack(raw)
        if magic != b"URMA3B01":
            sys.exit("bad header magic %r" % (magic,))
        if record_bytes != RECORD_BYTES:
            sys.exit("unexpected record size %d" % record_bytes)
        if side != 1:
            sys.exit("side=%d is not the reader side (1); target layout differs" % side)
        expect = HEADER.size + count * RECORD_BYTES + FOOTER.size
        if expect != size:
            print("WARNING: file size %d != expected %d (count=%d)" % (size, expect, count),
                  file=sys.stderr)
        footer = None
        if size >= expect:
            f.seek(expect)
            fmagic, fcount, fdropped = FOOTER.unpack(read_exact(f, FOOTER.size))
            footer = (fmagic, fcount, fdropped)
        f.seek(HEADER.size)

        hists = {name: new_hist() for name, _ in METRICS}
        n_total = 0
        n_valid = 0
        n_bad_seq = 0
        opcodes = {}
        read_bytes = 0
        limit = min(count, args.max_records) if args.max_records else count
        while n_total < limit:
            batch = min(65536, limit - n_total)
            chunk = read_exact(f, batch * RECORD_BYTES)
            for off in range(0, len(chunk), RECORD_BYTES):
                v = REC.unpack_from(chunk, off)
                n_total += 1
                opcodes[v[3]] = opcodes.get(v[3], 0) + 1
                read_bytes += v[5] * 512
                ihz, thz = v[6], v[15]
                roundtrip = ticks_to_us(v[11] - v[7], ihz) if v[11] >= v[7] else 0
                pre_send = ticks_to_us(v[8] - v[7], ihz) if v[8] >= v[7] else 0
                release = ticks_to_us(v[10] - v[9], ihz) if v[10] >= v[9] else 0
                add(hists["roundtrip_us"], roundtrip)
                add(hists["pre_send_us"], pre_send)
                add(hists["release_us"], release)
                valid = (
                    (v[13] & 2) != 0 and thz != 0 and v[22] == v[0]
                    and v[16] <= v[17] <= v[18] <= v[19] <= v[20] <= v[21]
                )
                if v[22] != v[0]:
                    n_bad_seq += 1
                if not valid:
                    continue
                n_valid += 1
                target = ticks_to_us(v[21] - v[16], thz)
                rx_buffer = ticks_to_us(v[17] - v[16], thz)
                buffer_exec = ticks_to_us(v[18] - v[17], thz)
                bdev = ticks_to_us(v[19] - v[18], thz)
                bdev_post = ticks_to_us(v[20] - v[19], thz)
                data = ticks_to_us(v[21] - v[20], thz)
                residual = max(roundtrip - target, 0)
                outside = max(residual - pre_send - release, 0)
                add(hists["target_us"], target)
                add(hists["rx_buffer_us"], rx_buffer)
                add(hists["buffer_exec_us"], buffer_exec)
                add(hists["bdev_us"], bdev)
                add(hists["bdev_post_us"], bdev_post)
                add(hists["data_us"], data)
                add(hists["residual_us"], residual)
                add(hists["outside_us"], outside)

    lines = []
    lines.append("file=%s" % args.path)
    lines.append("header: version=%d side=%d capacity=%d attempted=%d count=%d dropped=%d mode=%d"
                 % (version, side, capacity, attempted, count, dropped, mode))
    if footer:
        lines.append("footer: magic=%r count=%d dropped=%d"
                     % (footer[0].decode(errors="replace"), footer[1], footer[2]))
    lines.append("decoded=%d valid_target=%d bad_trace_seq=%d read_mib=%d"
                 % (n_total, n_valid, n_bad_seq, read_bytes // (1024 * 1024)))
    lines.append("opcodes=%s (2=READ)" % sorted(opcodes.items()))
    lines.append("")
    lines.append("%-16s %10s %8s %8s %8s %8s %10s %10s %10s" %
                 ("metric_us", "n", "mean", "p50", "p90", "p99", "p99.9", "max", "min"))
    for name, _kind in METRICS:
        h = hists[name]
        if h["n"] == 0:
            lines.append("%-16s %10d" % (name, 0))
            continue
        lines.append("%-16s %10d %8d %8d %8d %8d %10d %10d %10d" % (
            name, h["n"], h["sum"] // h["n"],
            percentile(h, 0.50), percentile(h, 0.90), percentile(h, 0.99),
            percentile(h, 0.999), h["mx"], h["mn"]))

    text = "\n".join(lines) + "\n"
    if args.out:
        with open(args.out, "w") as f:
            f.write(text)
        print(text, end="")
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
