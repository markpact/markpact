"""HTTP client for markpact.com portal API — mirrors public/client/markpact.py."""

from __future__ import annotations

import argparse
import json
import os
import secrets
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

CONFIG_DIR = Path.home() / ".markpact"
CONFIG_PATH = CONFIG_DIR / "config.json"
DEFAULT_KEY = Path.home() / ".ssh" / "markpact_ed25519"


def load_config() -> dict:
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    return {}


def save_config(config: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    try:
        os.chmod(CONFIG_PATH, 0o600)
    except OSError:
        pass


def host(value: str | None = None) -> str:
    cfg = load_config()
    h = value or cfg.get("host") or os.environ.get("MARKPACT_HOST") or "https://markpact.com"
    if not h.startswith(("http://", "https://")):
        h = "https://" + h
    return h.rstrip("/")


def token(value: str | None = None) -> str | None:
    return value or os.environ.get("MARKPACT_TOKEN") or os.environ.get("MARKPACT_API_TOKEN") or load_config().get("token")


def request(
    method: str,
    path: str,
    payload: dict | None = None,
    auth_token: str | None = None,
    host_value: str | None = None,
) -> dict:
    h = host(host_value)
    data = None
    headers = {"User-Agent": "markpact-portal-cli/0.1"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    t = token(auth_token)
    if t:
        headers["Authorization"] = "Bearer " + t
    req = urllib.request.Request(h + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            text = resp.read().decode("utf-8")
            return json.loads(text) if text else {"ok": True}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"HTTP {exc.code}: {body}") from exc


def command_init(args: argparse.Namespace) -> int:
    cfg = load_config()
    cfg["host"] = host(args.host)
    cfg["token"] = args.token
    save_config(cfg)
    result = request("GET", "/api/me", auth_token=args.token, host_value=args.host)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"Saved config: {CONFIG_PATH}")
    return 0


def command_me(args: argparse.Namespace) -> int:
    print(json.dumps(request("GET", "/api/me"), indent=2, ensure_ascii=False))
    return 0


def command_publish(args: argparse.Namespace) -> int:
    path = Path(args.file)
    content = path.read_text(encoding="utf-8")
    name = args.name or path.name.replace(".markpact.md", "")
    description = args.description or ""
    if args.ssh_key:
        result = publish_signed(content, name, description, Path(args.ssh_key))
    else:
        result = request("POST", "/api/publish", {"content": content, "name": name, "description": description})
    print(json.dumps(result, indent=2, ensure_ascii=False))
    pkg = result.get("package") or {}
    if pkg.get("raw_url"):
        print("Raw:", pkg["raw_url"], file=sys.stderr)
        slug = pkg.get("pack_slug") or name
        print("Fetch:", pkg.get("install_command", f"curl -fsSL {pkg['raw_url']} -o {slug}.markpact.md"), file=sys.stderr)
    return 0


def ssh_keygen() -> str:
    exe = shutil.which("ssh-keygen")
    if not exe:
        raise SystemExit("ssh-keygen is required for SSH key mode.")
    return exe


def command_keys_generate(args: argparse.Namespace) -> int:
    ssh_keygen()
    key = Path(args.path).expanduser() if args.path else DEFAULT_KEY
    key.parent.mkdir(parents=True, exist_ok=True)
    if key.exists() and not args.force:
        print(f"Key already exists: {key}")
    else:
        subprocess.check_call(
            ["ssh-keygen", "-t", "ed25519", "-f", str(key), "-N", "", "-C", args.comment or "markpact.com"]
        )
    print(f"Private key: {key}")
    print(f"Public key:  {key}.pub")
    return 0


def command_keys_add(args: argparse.Namespace) -> int:
    pub = Path(args.public_key).expanduser()
    content = pub.read_text(encoding="utf-8").strip()
    result = request("POST", "/api/ssh-keys", {"public_key": content, "name": args.name or pub.stem})
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def command_keys_list(args: argparse.Namespace) -> int:
    print(json.dumps(request("GET", "/api/ssh-keys"), indent=2, ensure_ascii=False))
    return 0


def key_fingerprint(key: Path) -> str:
    pub = Path(str(key) + ".pub")
    if not pub.exists():
        raise SystemExit(f"Missing public key: {pub}")
    out = subprocess.check_output(["ssh-keygen", "-l", "-f", str(pub)], text=True)
    for part in out.split():
        if part.startswith("SHA256:") or part.startswith("MD5:"):
            return part
    raise SystemExit("Could not parse SSH key fingerprint.")


def sign_message(key: Path, message: str) -> str:
    namespace = "markpact.com"
    tmp = CONFIG_DIR / f"sign-{secrets.token_hex(8)}.txt"
    tmp_sig = Path(str(tmp) + ".sig")
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    tmp.write_text(message, encoding="utf-8")
    try:
        subprocess.check_call(["ssh-keygen", "-Y", "sign", "-f", str(key), "-n", namespace, str(tmp)], stdout=subprocess.DEVNULL)
        return tmp_sig.read_text(encoding="utf-8")
    finally:
        try:
            tmp.unlink()
        except FileNotFoundError:
            pass
        try:
            tmp_sig.unlink()
        except FileNotFoundError:
            pass


def publish_message(content: str, name: str, description: str, timestamp: int, nonce: str) -> str:
    import hashlib

    return (
        "markpact-publish-v1\n"
        + str(timestamp)
        + "\n"
        + nonce
        + "\n"
        + hashlib.sha256(content.encode("utf-8")).hexdigest()
        + "\n"
        + name
        + "\n"
        + description
        + "\n"
    )


def command_release_register(args: argparse.Namespace) -> int:
    artifacts = []
    if args.artifacts_file:
        data = json.loads(Path(args.artifacts_file).read_text(encoding="utf-8"))
        artifacts = data.get("artifacts") if isinstance(data, dict) else data
    payload = {
        "contract_id": args.contract_id,
        "version": args.version,
        "artifact_index_url": args.artifact_index_url,
        "artifacts": artifacts,
    }
    if args.contract_digest:
        payload["contract_digest"] = args.contract_digest
    if args.contract_url:
        payload["contract_url"] = args.contract_url
    if args.source_git_commit:
        payload["source_git_commit"] = args.source_git_commit
    result = request("POST", "/api/releases", payload)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def command_release_get(args: argparse.Namespace) -> int:
    cid = urllib.parse.quote(args.contract_id, safe="")
    ver = urllib.parse.quote(args.version, safe="")
    result = request("GET", f"/api/contracts/{cid}/releases/{ver}")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def command_release_list(args: argparse.Namespace) -> int:
    cid = urllib.parse.quote(args.contract_id, safe="")
    result = request("GET", f"/api/contracts/{cid}/releases")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def publish_signed(content: str, name: str, description: str, key: Path) -> dict:
    ssh_keygen()
    key = key.expanduser()
    timestamp = int(time.time())
    nonce = secrets.token_hex(16)
    message = publish_message(content, name, description, timestamp, nonce)
    signature = sign_message(key, message)
    payload = {
        "content": content,
        "name": name,
        "description": description,
        "timestamp": timestamp,
        "nonce": nonce,
        "fingerprint": key_fingerprint(key),
        "signature": signature,
    }
    return request("POST", "/api/publish-signed", payload, auth_token=None)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="markpact portal")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("init")
    p.add_argument("--host", required=True)
    p.add_argument("--token", required=True)
    p.set_defaults(func=command_init)

    p = sub.add_parser("me")
    p.set_defaults(func=command_me)

    p = sub.add_parser("publish")
    p.add_argument("file")
    p.add_argument("--name")
    p.add_argument("--description")
    p.add_argument("--ssh-key")
    p.set_defaults(func=command_publish)

    keys = sub.add_parser("keys")
    ksub = keys.add_subparsers(dest="key_cmd", required=True)
    p = ksub.add_parser("generate")
    p.add_argument("--path")
    p.add_argument("--comment")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=command_keys_generate)
    p = ksub.add_parser("add")
    p.add_argument("public_key")
    p.add_argument("--name")
    p.set_defaults(func=command_keys_add)
    p = ksub.add_parser("list")
    p.set_defaults(func=command_keys_list)

    rel = sub.add_parser("release")
    rsub = rel.add_subparsers(dest="release_cmd", required=True)
    p = rsub.add_parser("register")
    p.add_argument("--contract-id", required=True)
    p.add_argument("--version", required=True)
    p.add_argument("--artifact-index-url", required=True)
    p.add_argument("--artifacts-file")
    p.add_argument("--contract-digest")
    p.add_argument("--contract-url")
    p.add_argument("--source-git-commit")
    p.set_defaults(func=command_release_register)
    p = rsub.add_parser("get")
    p.add_argument("--contract-id", required=True)
    p.add_argument("--version", required=True)
    p.set_defaults(func=command_release_get)
    p = rsub.add_parser("list")
    p.add_argument("--contract-id", required=True)
    p.set_defaults(func=command_release_list)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)
