import argparse
import json
import os
import socket
import threading
import time
from datetime import datetime, timezone

from protocol import build_message, recv_msgs, send_msg, validate_message

WORKER_REGISTRY = {}


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def log_event(group, origem, destino, msg_type, request_id, resultado):
    print(f"{group} | {origem} | {destino} | {msg_type} | {request_id} | {resultado}")


def load_or_create_config(path, host="127.0.0.1", port=9000, label="master"):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)

    config = {
        "uuid": __import__("uuid").uuid4().hex,
        "label": label,
        "host": host,
        "port": port,
    }
    with open(path, "w", encoding="utf-8") as file:
        json.dump(config, file, indent=2)
    return config


def register_worker(registry, worker_data):
    worker_uuid = worker_data["uuid"]
    registry[worker_uuid] = {
        "uuid": worker_uuid,
        "label": worker_data["label"],
        "host": worker_data.get("host"),
        "port": worker_data.get("port"),
        "last_seen": utc_timestamp(),
    }
    return registry[worker_uuid]


def registration_ack(config, worker_uuid, request_id, destination_label="worker"):
    payload = {
        "status": "registered",
        "worker_uuid": worker_uuid,
        "count": len(WORKER_REGISTRY),
    }
    return build_message(
        "registration_ack",
        payload,
        config["uuid"],
        config["label"],
        request_id=request_id,
    )


def handle_connection(conn, addr, config):
    group = config.get("group", "grupo-01")
    buffer = b""
    try:
        conn.settimeout(1.0)
        while True:
            try:
                messages, buffer = recv_msgs(conn, buffer)
            except socket.timeout:
                continue
            if not messages:
                continue

            for message in messages:
                if not validate_message(message):
                    log_event(group, "unknown", "master", "invalid_message", "-", "discarded")
                    continue

                msg_type = message["type"]
                origin = message["origin"]
                request_id = message["request_id"]

                if msg_type == "register_worker":
                    payload = message.get("payload", {})
                    worker_uuid = origin["uuid"]
                    label = origin["label"]
                    worker_record = register_worker(WORKER_REGISTRY, {
                        "uuid": worker_uuid,
                        "label": label,
                        "host": payload.get("host"),
                        "port": payload.get("port"),
                    })
                    ack = registration_ack(config, worker_uuid, request_id, label)
                    send_msg(conn, ack)
                    log_event(group, label, config["label"], msg_type, request_id, "registered")
                    log_event(group, config["label"], label, "registration_ack", request_id, worker_record["last_seen"])
                elif msg_type == "heartbeat":
                    log_event(group, origin["label"], config["label"], msg_type, request_id, "ok")
                elif msg_type == "echo":
                    response = build_message(
                        "echo",
                        {"status": "ok", "echo": message["payload"]},
                        config["uuid"],
                        config["label"],
                        request_id=request_id,
                    )
                    send_msg(conn, response)
                    log_event(group, origin["label"], config["label"], msg_type, request_id, "echoed")
                else:
                    log_event(group, origin["label"], config["label"], msg_type, request_id, "handled")
    except (ConnectionResetError, OSError):
        pass
    finally:
        conn.close()


def serve(host, port, config_path):
    config = load_or_create_config(config_path, host=host, port=port, label="master")
    config["group"] = "grupo-01"

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen(5)
    print(f"[master] escutando em {host}:{port}")

    try:
        while True:
            conn, addr = server.accept()
            thread = threading.Thread(target=handle_connection, args=(conn, addr, config), daemon=True)
            thread.start()
    finally:
        server.close()


def main():
    parser = argparse.ArgumentParser(description="Master do projeto P2P")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9000)
    parser.add_argument("--config", default="master_config.json")
    args = parser.parse_args()
    serve(args.host, args.port, args.config)


if __name__ == "__main__":
    main()
