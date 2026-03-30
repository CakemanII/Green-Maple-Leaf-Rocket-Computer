from typing import TypedDict
import json
import zlib
import lzma

import msgpack
import time

from rocket_gcs_communication import HAS_MSGPACK
from telemetry_data_transfer_types_retrieval import TelemetryDataTransferTypes

DataValue = float | bool | list[float | bool]

class TelemetryObject(TypedDict):
    label: str # label
    timestamp: float # timestamp in seconds
    data: DataValue # data payload

IntermediateRadioDataObject = tuple[float, list[tuple[str, list[float | bool]]]] | list[tuple[str, float, list[float | bool]]]

class DataCompression:
    LABEL_INTERATION_CODES: str = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/" # 64 unique characters for base64-like encoding of labels

    # Compression markers (first byte in payload)
    COMPRESS_NONE = b"N"
    COMPRESS_ZLIB = b"Z"
    COMPRESS_LZMA = b"L"

    @staticmethod
    def _compress_payload(raw_bytes: bytes) -> bytes:
        """Lossless adaptive compression: choose the smallest payload."""
        zlib_bytes = zlib.compress(raw_bytes, level=9)
        lzma_bytes = lzma.compress(raw_bytes, preset=(9 | lzma.PRESET_EXTREME))

        candidates = [
            (DataCompression.COMPRESS_NONE, raw_bytes),
            (DataCompression.COMPRESS_ZLIB, zlib_bytes),
            (DataCompression.COMPRESS_LZMA, lzma_bytes),
        ]

        marker, compressed = min(candidates, key=lambda pair: len(pair[1]))
        return marker + compressed

    @staticmethod
    def _decompress_payload(payload: bytes) -> bytes:
        """Reverse adaptive compression based on the leading marker byte."""
        if not payload:
            raise ValueError("Empty payload")

        marker = payload[:1]
        data = payload[1:]

        if marker == DataCompression.COMPRESS_NONE:
            return data
        if marker == DataCompression.COMPRESS_ZLIB:
            return zlib.decompress(data)
        if marker == DataCompression.COMPRESS_LZMA:
            return lzma.decompress(data)

        # Backward compatibility for old packets without marker
        return payload

    @staticmethod
    def _serialize_data(data_obj: dict) -> bytes:
        """Serialize to binary (MessagePack) or compact JSON. MessagePack is ~40% smaller."""
        if HAS_MSGPACK:
            return msgpack.packb(data_obj, use_bin_type=True)
        else:
            return json.dumps(data_obj, separators=(",", ":")).encode("utf-8")

    @staticmethod
    def _deserialize_data(data_bytes: bytes) -> dict:
        """Deserialize from binary (MessagePack) or JSON."""
        if HAS_MSGPACK:
            try:
                return msgpack.unpackb(data_bytes, raw=False)
            except Exception:
                # Fallback to JSON if MessagePack fails
                return json.loads(data_bytes.decode("utf-8"))
        else:
            return json.loads(data_bytes.decode("utf-8"))

    @staticmethod 
    def compress_data(datas: list[TelemetryObject], telemetry_data_transfer_types: TelemetryDataTransferTypes) -> str:
        # Convert and compress each individual label, and data object. (TELEOBJET -> LABEL BY CODE OBJET)
        compressed_data = []

        first_timestamp = None
        all_same_timestamp = True
        for data in datas:
            # Compress the label
            compressed_label = DataCompression._get_code_from_label(data["label"], telemetry_data_transfer_types)

            # Set the first timestamp or check
            if first_timestamp is None:
                first_timestamp = data["timestamp"]
            elif all_same_timestamp == True and data["timestamp"] != first_timestamp:
                all_same_timestamp = False

            # Get the data value
            data_value = data["data"] if not isinstance(data["data"], list) else [float(val) if isinstance(val, bool) else val for val in data["data"]]
            
            # Append the compressed label, relative timestamp, and data value to the compressed data list
            compressed_data.append((compressed_label, data_value + data["timestamp"]))

        data_with_sent_timestamp = (time.time(), compressed_data)

        # Convert to bytes
        byte_data = DataCompression._serialize_data(data_with_sent_timestamp)

        # Lossless adaptive compression for maximum size reduction
        fully_compressed_data = DataCompression._compress_payload(byte_data)

        # Encode to base64 for safe transmission as text
        return fully_compressed_data.hex()

    @staticmethod
    def _get_code_from_label(label: str, telemetry_data_transfer_types: TelemetryDataTransferTypes) -> str:
        """
        Returns a 2 character code for a given label.
        """
        label_split = label.split(".")
        if len(label_split) != 2:
            raise ValueError(f"Label '{label}' is not in the correct format 'category.label'")
        
        return DataCompression.LABEL_INTERATION_CODES[telemetry_data_transfer_types.get_index_of_category_and_label(label_split[0], label_split[1])[0]] + DataCompression.LABEL_INTERATION_CODES[telemetry_data_transfer_types.get_index_of_category_and_label(label_split[0], label_split[1])[1]]
