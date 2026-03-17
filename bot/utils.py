import subprocess
import re
import os
import pwd
import logging
import shlex
from html import unescape

import requests

from config import USER_MAPPING


class UserLoggerAdapter(logging.LoggerAdapter):
    """LoggerAdapter che aggiunge lo username ai log"""
    def process(self, msg, kwargs):
        username = self.extra.get('username', 'unknown')
        return f"[{username}] {msg}", kwargs


def get_logger(name, username='unknown'):
    """Ottiene un logger configurato con lo username dell'utente"""
    logger = logging.getLogger(name)
    return UserLoggerAdapter(logger, {'username': username})


CINECA_USER_SUPPORT_URL = "https://www.hpc.cineca.it/user-support/"


def strip_ansi_codes(text):
    """Rimuove i codici colore ANSI dall'output"""
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    return ansi_escape.sub("", text)


def get_process_owner(pid):
    """Ritorna il nome utente linux proprietario di un PID"""
    try:
        # Legge l'UID dalla cartella /proc
        stat_info = os.stat(f"/proc/{pid}")
        uid = stat_info.st_uid
        # Converte UID in username
        return pwd.getpwuid(uid).pw_name
    except (FileNotFoundError, KeyError, ValueError):
        return None


def get_linux_user(tg_id):
    return USER_MAPPING.get(tg_id)


def get_size_format(b, factor=1024, suffix="B"):
    """Converte byte in formato leggibile (es. 1.5GB)"""
    for unit in ["", "K", "M", "G", "T", "P"]:
        if b < factor:
            return f"{b:.1f}{unit}{suffix}"
        b /= factor
    return f"{b:.1f}P{suffix}"


def get_disk_space_report(path="/home", as_root=False):
    """Esegue du e ritorna l'output grezzo. as_root=True usa sudo per 'du'."""
    if not os.path.exists(path):
        return None

    # Scansione cartelle con du
    cmd = ["du", "-k", "--max-depth=1", path]
    if as_root:
        cmd = ["sudo", "-n"] + cmd

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        return result.stdout.strip()
    except Exception:
        return None


def get_active_users():
    """Ritorna utenti attivi (da who) con numero sessioni e host."""
    try:
        result = subprocess.run(["who"], capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            return []

        users = {}
        last_login_cache = {}

        def normalize_host(raw_host):
            host = (raw_host or "").strip()
            if not host:
                return "local"

            # Formato tipico locale: tmux(12345).%0 / screen(...)
            if host.startswith("tmux(") or host.startswith("screen("):
                return "tmux"

            if host in {":0", "localhost", "127.0.0.1"}:
                return "local"

            return host

        def pick_primary_host(hosts):
            if not hosts:
                return "local"

            remote_hosts = [h for h in hosts if h not in {"tmux", "local"}]
            if remote_hosts:
                return remote_hosts[0]

            if "tmux" in hosts:
                return "tmux"

            return hosts[0]

        def get_last_login_host(username):
            if username in last_login_cache:
                return last_login_cache[username]

            try:
                result_last = subprocess.run(
                    ["last", "-n", "20", "-w", username],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result_last.returncode != 0:
                    last_login_cache[username] = None
                    return None

                for raw in result_last.stdout.splitlines():
                    line = raw.strip()
                    if not line or line.lower().startswith("wtmp begins"):
                        continue

                    parts = line.split()
                    if len(parts) < 3 or parts[0] != username:
                        continue

                    candidate = parts[2].strip()
                    if candidate in {"-", ":0", "localhost", "127.0.0.1"}:
                        continue
                    if candidate.startswith("tmux(") or candidate.startswith("screen("):
                        continue
                    if candidate.lower() in {"still", "gone", "down"}:
                        continue

                    last_login_cache[username] = candidate
                    return candidate
            except Exception:
                pass

            last_login_cache[username] = None
            return None

        for raw_line in result.stdout.splitlines():
            line = raw_line.strip()
            if not line:
                continue

            parts = line.split()
            if not parts:
                continue

            username = parts[0]
            host = ""
            if "(" in line and ")" in line:
                host = line[line.find("(") + 1 : line.rfind(")")].strip()
            host = normalize_host(host)

            if username not in users:
                users[username] = {"username": username, "sessions": 0, "hosts": set()}

            users[username]["sessions"] += 1
            users[username]["hosts"].add(host)

        normalized = []
        for user_data in users.values():
            hosts = sorted(user_data["hosts"])
            primary_host = pick_primary_host(hosts)
            if primary_host in {"tmux", "local"}:
                fallback_host = get_last_login_host(user_data["username"])
                if fallback_host:
                    primary_host = fallback_host

            normalized.append(
                {
                    "username": user_data["username"],
                    "sessions": user_data["sessions"],
                    "hosts": hosts,
                    "host": primary_host,
                }
            )

        normalized.sort(key=lambda x: (-x["sessions"], x["username"]))
        return normalized
    except Exception:
        return []


def disconnect_user_temporarily(username, timeout_seconds=120):
    """Disconnette un utente e lo blocca per timeout_seconds, poi sblocca automaticamente."""
    safe_user = (username or "").strip()
    if not safe_user:
        return False, "Invalid username."

    # Evita input non previsto nel comando shell usato per lo sblocco ritardato.
    if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_.-]*[$]?$", safe_user):
        return False, "Invalid username format."

    try:
        # Termina processi/sessioni dell'utente.
        subprocess.run(
            ["sudo", "-n", "pkill", "-KILL", "-u", safe_user],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )

        lock = subprocess.run(
            ["sudo", "-n", "usermod", "-L", safe_user],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        if lock.returncode != 0:
            err = (lock.stderr or lock.stdout or "Unable to lock user.").strip()
            return False, err

        unlock_script = (
            f"sleep {int(timeout_seconds)}; "
            f"sudo -n usermod -U {shlex.quote(safe_user)} >/dev/null 2>&1"
        )
        subprocess.Popen(
            ["nohup", "bash", "-lc", unlock_script],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )

        return True, f"User {safe_user} disconnected and blocked for {int(timeout_seconds)} seconds."
    except Exception as exc:
        return False, str(exc)


def get_gpu_info():
    """
    Ottiene i processi GPU e ritorna una lista di dizionari.
    Ogni dizionario contiene: gpu_id, pid, user, gpu_memory, command
    """
    cmd = [
        "nvidia-smi",
        "--query-compute-apps=gpu_uuid,pid,used_memory",
        "--format=csv,noheader,nounits",
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            return []

        lines = result.stdout.strip().split("\n")

        if not lines or lines[0] == "":
            return []

        # Mappa UUID -> GPU ID
        gpu_uuid_to_id = {}
        try:
            uuid_result = subprocess.run(
                ["nvidia-smi", "--query-gpu=index,gpu_uuid", "--format=csv,noheader"],
                capture_output=True,
                text=True,
            )
            if uuid_result.returncode == 0:
                for line in uuid_result.stdout.strip().split("\n"):
                    parts = line.split(",")
                    if len(parts) == 2:
                        gpu_id = parts[0].strip()
                        gpu_uuid = parts[1].strip()
                        gpu_uuid_to_id[gpu_uuid] = gpu_id
        except Exception:
            pass

        processes = []

        for line in lines:
            parts = line.split(",")
            if len(parts) < 3:
                continue

            gpu_uuid = parts[0].strip()
            pid_str = parts[1].strip()

            if not pid_str.isdigit():
                continue

            # Ottieni GPU ID dalla UUID
            gpu_id = gpu_uuid_to_id.get(gpu_uuid, "?")

            # Ottieni owner del processo
            owner = get_process_owner(pid_str)
            if not owner:
                owner = "unknown"

            # Ottieni memoria VRAM
            try:
                vram_mib = float(parts[2].strip())
                vram_gb = vram_mib / 1024.0
                gpu_memory = f"{vram_gb:.2f}GB"
            except ValueError:
                gpu_memory = "N/A"

            # Recupera il comando completo
            cmd_full = "(non disponibile)"
            cmdline_path = f"/proc/{pid_str}/cmdline"
            try:
                with open(cmdline_path, "r", encoding="utf-8", errors="replace") as f:
                    raw = f.read()
                    cmd_full = raw.replace("\x00", " ").strip() or cmd_full
            except Exception:
                pass

            # Pulizia comando: rimuovi path completi, mostra solo il comando rilevante
            tokens = cmd_full.split()

            # Trova l'ultimo token che contiene uno slash (ultimo path)
            last_path_idx = -1
            for i, token in enumerate(tokens):
                if "/" in token:
                    last_path_idx = i

            # Se abbiamo trovato un path e ci sono token dopo, prendi quelli
            if last_path_idx >= 0 and last_path_idx < len(tokens) - 1:
                cmd_clean = " ".join(tokens[last_path_idx + 1 :])
            else:
                # Altrimenti mostra tutto
                cmd_clean = cmd_full

            # Se il comando è ancora molto lungo o vuoto, usa fallback
            if not cmd_clean.strip() or cmd_clean == "(non disponibile)":
                cmd_clean = cmd_full

            processes.append(
                {
                    "gpu_id": gpu_id,
                    "pid": pid_str,
                    "user": owner,
                    "gpu_memory": gpu_memory,
                    "command": cmd_clean,
                }
            )

        return processes

    except FileNotFoundError:
        return []
    except Exception:
        return []


def _clean_html_text(raw_text):
    """Converte frammenti HTML in testo pulito."""
    text = re.sub(r"<[^>]+>", " ", raw_text)
    text = unescape(text)
    return " ".join(text.split())


def get_leonardo_status():
    """
    Recupera lo stato di Leonardo dalla pagina User Support di CINECA.

    Ritorna:
    {
        "active_sem": "sem1" | "sem2" | "sem3" | None,
        "status_label": "UP" | "DEGRADED" | "DOWN" | "UNKNOWN",
        "power_state": "ON" | "DEGRADED" | "OFF" | "UNKNOWN",
        "dots": {"sem1": bool, "sem2": bool, "sem3": bool},
        "info_status": str,
        "source_url": str,
    }
    """
    try:
        response = requests.get(CINECA_USER_SUPPORT_URL, timeout=15)
        response.raise_for_status()
    except requests.RequestException as exc:
        return {"error": f"Impossibile contattare CINECA: {exc}"}

    html_page = response.text

    # Cerca il blocco specifico del link hardware/leonardo seguito dal suo infostatus.
    pattern = re.compile(
        r'<a href="[^\"]*?/systems/hardware/leonardo/?[^\"]*">\s*(?P<body>.*?)</a>\s*'
        r'<div class="infostatus">(?P<info>.*?)</div>',
        re.IGNORECASE | re.DOTALL,
    )
    match = pattern.search(html_page)
    if not match:
        return {"error": "Blocco stato Leonardo non trovato nella pagina CINECA."}

    body = match.group("body")
    info_status = _clean_html_text(match.group("info"))

    dots = {}
    for sem in ("sem1", "sem2", "sem3"):
        sem_match = re.search(
            rf"<span class=['\"]{sem}(?P<extra>[^'\"]*)['\"]></span>",
            body,
            flags=re.IGNORECASE,
        )
        extra_classes = sem_match.group("extra") if sem_match else ""
        dots[sem] = "active" in extra_classes.split()

    active_sem = next((sem for sem in ("sem1", "sem2", "sem3") if dots.get(sem)), None)

    status_map = {
        "sem1": ("UP", "ON"),
        "sem2": ("DEGRADED", "DEGRADED"),
        "sem3": ("DOWN", "OFF"),
        None: ("UNKNOWN", "UNKNOWN"),
    }
    status_label, power_state = status_map.get(active_sem, ("UNKNOWN", "UNKNOWN"))

    return {
        "active_sem": active_sem,
        "status_label": status_label,
        "power_state": power_state,
        "dots": dots,
        "info_status": info_status or "Nessuna descrizione disponibile.",
        "source_url": CINECA_USER_SUPPORT_URL,
    }
