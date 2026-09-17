import json
import socket
import uuid
from datetime import datetime, timezone

REQUIRED_FIELDS = {"type", "msg_id", "request_id", "origin", "timestamp", "payload"}


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def build_message(message_type, payload, origin_uuid, origin_label, request_id=None, msg_id=None):
    if request_id is None:
        request_id = uuid.uuid4().hex
    if msg_id is None:
        msg_id = uuid.uuid4().hex

    return {
        "type": message_type,
        "msg_id": msg_id,
        "request_id": request_id,
        "origin": {
            "uuid": origin_uuid,
            "label": origin_label,
        },
        "timestamp": utc_timestamp(),
        "payload": payload,
    }


def validate_message(message):
    if not isinstance(message, dict):
        return False

    if not REQUIRED_FIELDS.issubset(message.keys()):
        return False

    if not isinstance(message["type"], str) or not message["type"].strip():
        return False

    if not isinstance(message["msg_id"], str) or not message["msg_id"].strip():
        return False

    if not isinstance(message["request_id"], str) or not message["request_id"].strip():
        return False

    if not isinstance(message["origin"], dict):
        return False

    origin = message["origin"]
    if not isinstance(origin.get("uuid"), str) or not origin["uuid"].strip():
        return False
    if not isinstance(origin.get("label"), str) or not origin["label"].strip():
        return False

    if not isinstance(message["timestamp"], str) or not message["timestamp"].strip():
        return False

    return True


def send_msg(sock, message):
    if not validate_message(message):
        raise ValueError("Mensagem inválida: campos obrigatórios ausentes ou incorretos.")

    serialized = json.dumps(message, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    sock.sendall(serialized + b"\n")
    return len(serialized) + 1


def recv_msgs(sock, buffer=None):
    return_tuple = buffer is not None
    if buffer is None:
        buffer = b""
    if isinstance(buffer, str):
        buffer = buffer.encode("utf-8")

    data = bytearray(buffer)
    messages = []

    while True:
        try:
            chunk = sock.recv(4096)
        except (BlockingIOError, socket.timeout):
            break
        except OSError:
            break

        if not chunk:
            break

        data.extend(chunk)

        while True:
            newline_index = data.find(b"\n")
            if newline_index < 0:
                break

            raw_line = bytes(data[:newline_index]).strip()
            del data[: newline_index + 1]

            if not raw_line:
                continue

            try:
                decoded = raw_line.decode("utf-8")
                parsed = json.loads(decoded)
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue

            if validate_message(parsed):
                messages.append(parsed)

    remaining = bytes(data)
    if return_tuple:
        return messages, remaining
    return messages
