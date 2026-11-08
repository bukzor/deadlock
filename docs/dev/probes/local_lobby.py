"""Build a `citadel_start_local_bot_match` payload that puts you on the team you choose.

Prototype (2026-11-05). Only you go in the payload: fake members block the start
("waiting on 11 players"), since bot takeover of disconnects is developmentonly.
See docs/dev/game-runtime.kb/local-bot-match-lobby.md.

usage: local_lobby.py ACCOUNT_ID NAME HERO_ID [--team 0|1] [--cfg PATH]
"""

import argparse
import random
import struct
from pathlib import Path

MATCH_MODE_PRIVATE_LOBBY = 2  # the only mode the server accepts
GAME_MODE_NORMAL = 1
BOT_DIFFICULTY_HARD = 3


def varint(n):
    out = bytearray()
    while True:
        byte, n = n & 0x7F, n >> 7
        out.append(byte | (0x80 if n else 0))
        if not n:
            return bytes(out)


def field_varint(num, value):
    return varint(num << 3) + varint(value)


def field_bytes(num, data):
    return varint(num << 3 | 2) + varint(len(data)) + data


def member(account_id, name, team, hero_id):
    return (
        field_varint(1, account_id)
        + field_bytes(2, name.encode())
        + field_varint(3, team)
        + field_varint(5, hero_id)
        + field_varint(6, 0)
    )


def payload(handshake, members):
    lobby = field_varint(3, MATCH_MODE_PRIVATE_LOBBY) + field_varint(4, GAME_MODE_NORMAL)
    static = b"".join(field_bytes(6, member(*m)) for m in members) + field_varint(9, BOT_DIFFICULTY_HARD)
    return varint(1 << 3 | 1) + struct.pack("<Q", handshake) + field_bytes(2, lobby) + field_bytes(3, static)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("account_id", type=int)
    ap.add_argument("name")
    ap.add_argument("hero_id", type=int)
    ap.add_argument("--team", type=int, choices=(0, 1), default=0, help="0 Hidden King, 1 Archmother")
    ap.add_argument("--cfg", type=Path, help="also write an exec-able cfg here")
    args = ap.parse_args()
    hexstr = payload(random.getrandbits(63) | 1, [(args.account_id, args.name, args.team, args.hero_id)]).hex()
    print(hexstr)
    if args.cfg:
        args.cfg.write_text(f"citadel_start_local_bot_match {hexstr}\n")


if __name__ == "__main__":
    main()
