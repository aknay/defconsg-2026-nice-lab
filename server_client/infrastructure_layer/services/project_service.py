import gc

import numpy as np
import os

import psutil

from domain.entities import InputTraceBatch
from server_client.infrastructure_layer.h5_trace_repository import H5TraceRepository


class ProjectFileService:

    def __init__(self, file_path: str):
        self._h5_trace_repository = None
        self._key = None
        self._total_trace_count = 0
        self._file_path = file_path

    def init(self, key: bytes, total_trace_count: int):
        self._total_trace_count = total_trace_count

        dir_path = os.path.dirname(self._file_path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)

        target = os.path.abspath(self._file_path)

        # to release pid holding any python
        for proc in psutil.process_iter(["pid", "name"]):
            if proc.info["name"] != "python.exe":
                continue

            try:
                files = proc.open_files()
                if any(f.path == target for f in files):
                    proc.kill()
                    break  # ✅ stop immediately
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                pass

        # --- Step 2: Remove existing file if it exists ---
        if os.path.exists(self._file_path):
            try:
                os.remove(self._file_path)
                print(f"Removed existing file: {self._file_path}")
            except PermissionError:
                raise RuntimeError(
                    f"Cannot delete {self._file_path}. Close any open handles first."
                )

        # --- Step 3: Initialize new repository (file is created immediately) ---
        self._h5_trace_repository = H5TraceRepository(
            file_path=self._file_path, total_traces=self._total_trace_count
        )
        self._key = key
        print(f"Initialized fresh repository: {self._file_path}")

    def save_trace(self, trace: np.ndarray, hex: bytes):
        trace = trace.reshape(1, -1)
        plaintext = np.frombuffer(hex, dtype=np.uint8).reshape(1, -1)
        key = np.frombuffer(self._key, dtype=np.uint8).reshape(1, -1)

        metadata = {
            "key": key,
            "plain_text": plaintext,
            "cipher_text": plaintext,
        }

        current_batch = InputTraceBatch(traces=trace, metadata=metadata)

        self._h5_trace_repository.save_batch(current_batch)
