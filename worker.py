import argparse
import json
import os
import socket
import time
import uuid

from protocol import build_message, recv_msgs, send_msg, validate_message


def load_or_create_config(path, host="127.0.0.1", port=9000, label=None):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)

    if label is None:
        label = f"worker-{uuid.uuid4().hex[:8]}"

    config = {
        "uuid": uuid.uuid4().hex,
        "label": label,
        "host": host,
        "port": port,
    }
    with open(path, "w", encoding="utf-8") as file:
        json.dump(config, file, indent=2)
    return config


def register_with_master(config, master_host, master_port):
    message = build_message(
        "register_worker",
        {"status": "ready", "host": config["host"], "port": config["port"]},
        config["uuid"],
        config["label"],
        request_id=f"register-{uuid.uuid4().hex[:8]}",
    )
    sock = socket.create_connection((master_host, master_port), timeout=5)
    send_msg(sock, message)

    data = b""
    while True:
        try:
            messages, data = recv_msgs(sock, data)
        except socket.timeout:
            break
        if not messages:
            continue
        for item in messages:
            if validate_message(item) and item["type"] == "registration_ack":
                return sock, item
        break

    return sock, None


def main():
    parser = argparse.ArgumentParser(description="Worker do projeto P2P")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9000)
    parser.add_argument("--label", default=None)
    parser.add_argument("--config", default="worker_config.json")
    args = parser.parse_args()

    config = load_or_create_config(args.config, host=args.host, port=args.port, label=args.label)
    print(f"[worker] {config['label']} ({config['uuid']}) conectado em {config['host']}:{config['port']}")

    sock, ack = register_with_master(config, args.host, args.port)
    if ack is None:
        print("[worker] não recebeu acknowledgment do master")
        return

    print(f"[worker] registro confirmado: {ack['payload']}")

    for index in range(3):
        heartbeat = build_message(
            "heartbeat",
            {"status": "alive", "seq": index},
            config["uuid"],
            config["label"],
            request_id=f"hb-{uuid.uuid4().hex[:8]}",
        )
        send_msg(sock, heartbeat)
        time.sleep(1)

        echo_message = build_message(
            "echo",
            {"value": f"hello-{index}"},
            config["uuid"],
            config["label"],
            request_id=f"echo-{uuid.uuid4().hex[:8]}",
        )
        send_msg(sock, echo_message)
        time.sleep(1)

    sock.close()


if __name__ == "__main__":
    main()
