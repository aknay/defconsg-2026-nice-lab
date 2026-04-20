import struct
from typing import Optional

import numpy as np
import paho.mqtt.client as mqtt
from Crypto.Cipher import AES

from server_client.infrastructure_layer.services.project_service import (
    ProjectFileService,
)


class Watcher:
    TYPE_INIT = 1
    TYPE_DATA = 2
    VERSION = 1

    def __init__(
        self,
        project_file_service: ProjectFileService,
        broker="broker.hivemq.com",
        port=1883,
        known_key: Optional[str] = None,
    ):
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        self.broker = broker
        self.port = port

        # State
        self.total_items = None
        self.received_count = 0

        self._project_file_service = project_file_service

        if known_key:
            if len(known_key) != 16:
                raise ValueError("The key must be 16 characters long")

            self._known_key = known_key.encode("utf-8")
        else:
            self._known_key = None

    # -------------------------
    # MQTT lifecycle
    # -------------------------
    def start(self):
        self.client.connect(self.broker, self.port)
        self.client.loop_forever()

    def on_connect(self, client, userdata, flags, rc, properties):
        print("🕵️ Watcher is Online. Monitoring 'incoming'...")
        client.subscribe("serverB/incoming")

    def on_message(self, client, userdata, msg):
        raw = msg.payload

        # Basic validation
        if len(raw) < 8:
            print("❌ Payload too short")
            return

        msg_type, version, flags, length = struct.unpack("BBHI", raw[:8])
        payload = raw[8 : 8 + length]

        if msg_type == self.TYPE_INIT:
            self.handle_init(payload)

        elif msg_type == self.TYPE_DATA:
            self.handle_data(payload)

        else:
            print("❌ Unknown message type")

    # -------------------------
    # Handlers
    # -------------------------
    def handle_init(self, payload: bytes):
        if len(payload) < 20:
            print("❌ INIT payload too short")
            return

        key = payload[:16]
        total_items = struct.unpack("I", payload[16:20])[0]

        self.total_items = total_items
        self.received_count = 0

        print("init project")
        self._project_file_service.init(key, total_items)
        print("init done")

    def handle_data(self, payload: bytes):
        if len(payload) < 20:
            print("❌ DATA payload too short")
            return
        header = payload[:16]
        hex_data = payload[:16]
        if self._known_key is not None:
            header = self.decrypt_16_bytes(header)

        wave_len = struct.unpack("I", payload[16:20])[0]
        wave_bytes = payload[20 : 20 + wave_len]

        waveform = np.frombuffer(wave_bytes, dtype=np.float32)

        self.received_count += 1

        # print(f"📈 Waveform: {waveform.shape}")
        if self._known_key:
            print(f"🔓 Decrypted: {self.to_human_readable(header)}")
        else:
            print(f"🔑 Encrypted: {header.hex(' ').upper()}")
        print(f"📦 Progress: {self.received_count}/{self.total_items}")
        self._project_file_service.save_trace(waveform, hex_data)

    @staticmethod
    def to_human_readable(data: bytes) -> str:
        # Try UTF-8 first
        try:
            text = data.decode("utf-8")
            # Check if it's mostly printable
            if all(32 <= ord(c) < 127 for c in text):
                return text
        except UnicodeDecodeError:
            pass

        # Fallback: show hex (clean format)
        return data.hex(" ").upper()

    def decrypt_16_bytes(self, data: bytes) -> bytes:
        if self._known_key is None:
            return data

        if len(data) != 16:
            raise ValueError("AES block must be 16 bytes")

        cipher = AES.new(self._known_key, AES.MODE_ECB)
        return cipher.decrypt(data)

    # -------------------------
    # Optional helpers
    # -------------------------
    @staticmethod
    def parse_header(raw: bytes):
        return struct.unpack("BBHI", raw[:8])


if __name__ == "__main__":
    project_file_service = ProjectFileService(file_path="project_file/project_file.sx")
    server = Watcher(project_file_service)
    server.start()
