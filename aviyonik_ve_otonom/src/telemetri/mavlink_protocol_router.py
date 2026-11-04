#!/usr/bin/env python3
"""
AIAA DBF 2027 - MAVLink v2 Protocol Router & Micro-Telemetry Bridge
Provides native, zero-external-dependency MAVLink v2 packet framing, encoding, decoding,
X.25 CRC validation, and command routing compatible with QGroundControl, Mission Planner,
and companion computers.
"""

import struct
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Union


def x25_crc(data: bytes, crc: int = 0xFFFF) -> int:
    """Computes X.25 / MCRF4XX 16-bit CRC for MAVLink packet verification."""
    for byte in data:
        tmp = byte ^ (crc & 0xFF)
        tmp = (tmp ^ (tmp << 4)) & 0xFF
        crc = (crc >> 8) ^ (tmp << 8) ^ (tmp << 3) ^ (tmp >> 4)
        crc &= 0xFFFF
    return crc


@dataclass
class MAVLinkMessage:
    msg_id: int
    msg_name: str
    sys_id: int
    comp_id: int
    seq: int
    payload_dict: Dict[str, Any]
    raw_payload: bytes


class MAVLinkProtocolRouter:
    """
    MAVLink v2 Packet Encoder, Decoder, and Stream Router.
    """

    MAGIC_V2 = 0xFD

    # CRC Extra seeds for supported standard MAVLink messages
    CRC_EXTRA_MAP = {
        0: 50,     # HEARTBEAT
        30: 39,    # ATTITUDE
        33: 104,   # GLOBAL_POSITION_INT
        76: 152,   # COMMAND_LONG
        147: 154,  # BATTERY_STATUS
        253: 83,   # STATUSTEXT
    }

    MSG_NAME_MAP = {
        0: "HEARTBEAT",
        30: "ATTITUDE",
        33: "GLOBAL_POSITION_INT",
        76: "COMMAND_LONG",
        147: "BATTERY_STATUS",
        253: "STATUSTEXT",
    }

    def __init__(self, sys_id: int = 1, comp_id: int = 1):
        self.sys_id = sys_id
        self.comp_id = comp_id
        self.seq = 0
        self.rx_buffer = bytearray()
        self.routed_commands: List[Dict[str, Any]] = []

    def _next_seq(self) -> int:
        cur = self.seq
        self.seq = (self.seq + 1) % 256
        return cur

    def encode_packet(self, msg_id: int, payload: bytes) -> bytes:
        """
        Frames an arbitrary payload into a standard MAVLink v2 binary packet:
        [MAGIC(1) | LEN(1) | INC_FLAGS(1) | CMP_FLAGS(1) | SEQ(1) | SYS(1) | COMP(1) | MSG_ID(3) | PAYLOAD(N) | CRC(2)]
        """
        seq = self._next_seq()
        payload_len = len(payload)
        incompat_flags = 0
        compat_flags = 0

        # Message ID is 3 bytes little-endian
        msg_id_bytes = struct.pack("<I", msg_id)[:3]

        header = struct.pack(
            "<BBBBBB",
            self.MAGIC_V2,
            payload_len,
            incompat_flags,
            compat_flags,
            seq,
            self.sys_id,
        ) + bytes([self.comp_id]) + msg_id_bytes

        crc_extra = self.CRC_EXTRA_MAP.get(msg_id, 0)
        # CRC is calculated over header (excluding magic byte 0xFD), payload, and crc_extra
        crc_data = header[1:] + payload + bytes([crc_extra])
        checksum = x25_crc(crc_data)

        return header + payload + struct.pack("<H", checksum)

    def encode_heartbeat(self,
                         mav_type: int = 1,  # 1 = MAV_TYPE_FIXED_WING
                         autopilot: int = 3, # 3 = MAV_AUTOPILOT_ARDUPILOTMEGA
                         base_mode: int = 209,
                         custom_mode: int = 0,
                         system_status: int = 4) -> bytes:
        """Encodes MAVLink #0 HEARTBEAT packet."""
        payload = struct.pack(
            "<IBBBBB",
            custom_mode,
            mav_type,
            autopilot,
            base_mode,
            system_status,
            3 # MAVLink version
        )
        return self.encode_packet(0, payload)

    def encode_attitude(self,
                        time_boot_ms: int,
                        roll_rad: float,
                        pitch_rad: float,
                        yaw_rad: float,
                        rollspeed_rad_s: float = 0.0,
                        pitchspeed_rad_s: float = 0.0,
                        yawspeed_rad_s: float = 0.0) -> bytes:
        """Encodes MAVLink #30 ATTITUDE packet."""
        payload = struct.pack(
            "<Iffffff",
            time_boot_ms,
            roll_rad,
            pitch_rad,
            yaw_rad,
            rollspeed_rad_s,
            pitchspeed_rad_s,
            yawspeed_rad_s
        )
        return self.encode_packet(30, payload)

    def encode_global_position_int(self,
                                   time_boot_ms: int,
                                   lat_deg: float,
                                   lon_deg: float,
                                   alt_msl_m: float,
                                   relative_alt_m: float,
                                   vx_ms: float,
                                   vy_ms: float,
                                   vz_ms: float,
                                   heading_deg: float) -> bytes:
        """Encodes MAVLink #33 GLOBAL_POSITION_INT packet."""
        lat_int = int(lat_deg * 1e7)
        lon_int = int(lon_deg * 1e7)
        alt_mm = int(alt_msl_m * 1000.0)
        rel_alt_mm = int(relative_alt_m * 1000.0)
        vx_cms = int(vx_ms * 100.0)
        vy_cms = int(vy_ms * 100.0)
        vz_cms = int(vz_ms * 100.0)
        hdg_cdeg = int((heading_deg % 360.0) * 100.0)

        payload = struct.pack(
            "<IiiiihhhH",
            time_boot_ms,
            lat_int,
            lon_int,
            alt_mm,
            rel_alt_mm,
            vx_cms,
            vy_cms,
            vz_cms,
            hdg_cdeg
        )
        return self.encode_packet(33, payload)

    def encode_statustext(self, severity: int, text: str) -> bytes:
        """Encodes MAVLink #253 STATUSTEXT packet."""
        text_bytes = text.encode("utf-8")[:50].ljust(50, b"\x00")
        payload = struct.pack("<B50s", severity, text_bytes)
        return self.encode_packet(253, payload)

    def encode_battery_status(self,
                              voltage_v: float,
                              current_a: float,
                              consumed_mah: float,
                              battery_remaining_pct: float) -> bytes:
        """Encodes MAVLink #147 BATTERY_STATUS packet."""
        consumed_mah_int = int(consumed_mah)
        current_ca = int(current_a * 100.0)
        cell_mv = int((voltage_v / 6.0) * 1000.0)
        voltages = [cell_mv] * 6 + [65535] * 4  # 6S pack, pad to 10 cells

        payload = struct.pack(
            "<iih10HBB",
            0, # current_consumed (deprecated / not used)
            consumed_mah_int,
            current_ca,
            *voltages,
            1, # battery type LiPo
            int(battery_remaining_pct)
        )
        return self.encode_packet(147, payload)

    def decode_packet(self, packet_bytes: bytes) -> Optional[MAVLinkMessage]:
        """
        Validates MAVLink v2 packet and extracts header & typed payload.
        Returns MAVLinkMessage or None if invalid checksum / framing.
        """
        if len(packet_bytes) < 12:
            return None

        magic, payload_len, incompat, compat, seq, sys_id = struct.unpack("<BBBBBB", packet_bytes[:6])
        if magic != self.MAGIC_V2:
            return None

        comp_id = packet_bytes[6]
        msg_id_bytes = packet_bytes[7:10] + b"\x00"
        msg_id = struct.unpack("<I", msg_id_bytes)[0]

        total_len = 10 + payload_len + 2
        if len(packet_bytes) < total_len:
            return None

        payload = packet_bytes[10:10 + payload_len]
        rx_crc = struct.unpack("<H", packet_bytes[10 + payload_len:total_len])[0]

        crc_extra = self.CRC_EXTRA_MAP.get(msg_id, 0)
        crc_data = packet_bytes[1:10 + payload_len] + bytes([crc_extra])
        expected_crc = x25_crc(crc_data)

        if rx_crc != expected_crc:
            return None  # Checksum mismatch

        # Parse payload dictionary
        payload_dict = self._parse_payload_dict(msg_id, payload)

        return MAVLinkMessage(
            msg_id=msg_id,
            msg_name=self.MSG_NAME_MAP.get(msg_id, f"UNKNOWN_{msg_id}"),
            sys_id=sys_id,
            comp_id=comp_id,
            seq=seq,
            payload_dict=payload_dict,
            raw_payload=payload
        )

    def _parse_payload_dict(self, msg_id: int, payload: bytes) -> Dict[str, Any]:
        """Maps binary payload to field dictionary."""
        d = {}
        try:
            if msg_id == 0:  # HEARTBEAT
                custom_mode, mav_type, autopilot, base_mode, sys_status, v = struct.unpack("<IBBBBB", payload[:9])
                d = {
                    "custom_mode": custom_mode,
                    "mav_type": mav_type,
                    "autopilot": autopilot,
                    "base_mode": base_mode,
                    "system_status": sys_status,
                }
            elif msg_id == 30:  # ATTITUDE
                t_boot, r, p, y, rs, ps, ys = struct.unpack("<Iffffff", payload[:28])
                d = {
                    "time_boot_ms": t_boot,
                    "roll": r,
                    "pitch": p,
                    "yaw": y,
                    "rollspeed": rs,
                    "pitchspeed": ps,
                    "yawspeed": ys,
                }
            elif msg_id == 33:  # GLOBAL_POSITION_INT
                t_boot, lat, lon, alt, rel_alt, vx, vy, vz, hdg = struct.unpack("<IiiiihhhH", payload[:28])
                d = {
                    "time_boot_ms": t_boot,
                    "lat_deg": lat / 1e7,
                    "lon_deg": lon / 1e7,
                    "alt_msl_m": alt / 1000.0,
                    "relative_alt_m": rel_alt / 1000.0,
                    "vx_ms": vx / 100.0,
                    "vy_ms": vy / 100.0,
                    "vz_ms": vz / 100.0,
                    "heading_deg": hdg / 100.0,
                }
            elif msg_id == 76:  # COMMAND_LONG
                p1, p2, p3, p4, p5, p6, p7, cmd, tgt_sys, tgt_comp, conf = struct.unpack("<fffffffHBBB", payload[:33])
                d = {
                    "command": cmd,
                    "target_system": tgt_sys,
                    "target_component": tgt_comp,
                    "params": [p1, p2, p3, p4, p5, p6, p7],
                    "confirmation": conf,
                }
            elif msg_id == 253:  # STATUSTEXT
                severity, text_raw = struct.unpack("<B50s", payload[:51])
                d = {
                    "severity": severity,
                    "text": text_raw.decode("utf-8", errors="ignore").rstrip("\x00"),
                }
        except Exception:
            pass
        return d

    def parse_stream(self, incoming_bytes: bytes) -> List[MAVLinkMessage]:
        """
        Parses a stream of raw incoming bytes from UDP/Serial, extracts valid packets,
        and manages internal ring buffer.
        """
        self.rx_buffer.extend(incoming_bytes)
        parsed_msgs = []

        while len(self.rx_buffer) >= 12:
            # Look for magic byte
            if self.rx_buffer[0] != self.MAGIC_V2:
                self.rx_buffer.pop(0)
                continue

            payload_len = self.rx_buffer[1]
            total_expected_len = 10 + payload_len + 2

            if len(self.rx_buffer) < total_expected_len:
                break  # Wait for more bytes

            candidate = bytes(self.rx_buffer[:total_expected_len])
            msg = self.decode_packet(candidate)

            if msg is not None:
                parsed_msgs.append(msg)
                if msg.msg_id == 76:
                    self.routed_commands.append(msg.payload_dict)
                del self.rx_buffer[:total_expected_len]
            else:
                # Corrupted header or false magic byte
                self.rx_buffer.pop(0)

        return parsed_msgs
