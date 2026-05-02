#!/usr/bin/env python3
"""
system_health_check.py - Monitor de Saúde do Sistema
Verifica CPU, memória, disco e processos críticos.
Gera relatório JSON e salva histórico de logs.
"""

import json
import logging
import platform
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

try:
    import psutil
except ImportError:
    print("ERRO: instale psutil com: pip install psutil", file=sys.stderr)
    sys.exit(1)

# ---------------------------------------------------------------------------
# Configuração de logging
# ---------------------------------------------------------------------------

LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_DIR / "system_health.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Limiares de alerta
# ---------------------------------------------------------------------------

THRESHOLDS = {
    "cpu_percent": 90.0,
    "memory_percent": 80.0,
    "disk_percent": 85.0,
}

# Processos críticos a monitorar (ajuste conforme seu ambiente)
CRITICAL_PROCESSES = [
    "python3", "python",
]

# ---------------------------------------------------------------------------
# Coleta de métricas
# ---------------------------------------------------------------------------


def collect_cpu() -> dict:
    """Coleta uso de CPU (global e por core)."""
    per_core = psutil.cpu_percent(interval=1, percpu=True)
    global_pct = sum(per_core) / len(per_core)
    freq = psutil.cpu_freq()
    return {
        "global_percent": round(global_pct, 2),
        "per_core_percent": [round(c, 2) for c in per_core],
        "logical_cores": psutil.cpu_count(logical=True),
        "physical_cores": psutil.cpu_count(logical=False),
        "frequency_mhz": round(freq.current, 2) if freq else None,
        "alert": global_pct >= THRESHOLDS["cpu_percent"],
    }


def collect_memory() -> dict:
    """Coleta uso de memória RAM e swap."""
    ram = psutil.virtual_memory()
    swap = psutil.swap_memory()
    return {
        "ram": {
            "total_gb": round(ram.total / 1e9, 2),
            "available_gb": round(ram.available / 1e9, 2),
            "used_gb": round(ram.used / 1e9, 2),
            "percent": ram.percent,
            "alert": ram.percent >= THRESHOLDS["memory_percent"],
        },
        "swap": {
            "total_gb": round(swap.total / 1e9, 2),
            "used_gb": round(swap.used / 1e9, 2),
            "percent": swap.percent,
        },
    }


def collect_disk() -> dict:
    """Coleta uso de disco para todas as partições montadas."""
    partitions = []
    for part in psutil.disk_partitions(all=False):
        try:
            usage = psutil.disk_usage(part.mountpoint)
            partitions.append({
                "device": part.device,
                "mountpoint": part.mountpoint,
                "fstype": part.fstype,
                "total_gb": round(usage.total / 1e9, 2),
                "used_gb": round(usage.used / 1e9, 2),
                "free_gb": round(usage.free / 1e9, 2),
                "percent": usage.percent,
                "alert": usage.percent >= THRESHOLDS["disk_percent"],
            })
        except PermissionError:
            continue
    return {"partitions": partitions}


def collect_processes(critical_names: list[str]) -> dict:
    """Verifica se processos críticos estão rodando e lista os top 5 por CPU."""
    running_critical = []
    for proc in psutil.process_iter(["name", "pid", "status"]):
        try:
            if proc.info["name"] and any(
                cn.lower() in proc.info["name"].lower() for cn in critical_names
            ):
                running_critical.append({
                    "name": proc.info["name"],
                    "pid": proc.info["pid"],
                    "status": proc.info["status"],
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    missing = [
        name for name in critical_names
        if not any(name.lower() in p["name"].lower() for p in running_critical)
    ]

    # Top 5 processos por uso de CPU
    top_procs = []
    for proc in psutil.process_iter(["name", "pid", "cpu_percent", "memory_percent"]):
        try:
            top_procs.append({
                "name": proc.info["name"],
                "pid": proc.info["pid"],
                "cpu_percent": proc.info["cpu_percent"],
                "memory_percent": round(proc.info.get("memory_percent") or 0.0, 2),
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    top_procs = sorted(top_procs, key=lambda p: p["cpu_percent"] or 0, reverse=True)[:5]

    return {
        "critical_monitored": critical_names,
        "critical_running": running_critical,
        "critical_missing": missing,
        "top5_by_cpu": top_procs,
        "alert": len(missing) > 0,
    }


def collect_network() -> dict:
    """Coleta estatísticas de rede (bytes enviados/recebidos desde o boot)."""
    net = psutil.net_io_counters()
    return {
        "bytes_sent_mb": round(net.bytes_sent / 1e6, 2),
        "bytes_recv_mb": round(net.bytes_recv / 1e6, 2),
        "packets_sent": net.packets_sent,
        "packets_recv": net.packets_recv,
        "errors_in": net.errin,
        "errors_out": net.errout,
    }


def collect_system_info() -> dict:
    """Coleta informações estáticas do sistema operacional."""
    boot_time = datetime.fromtimestamp(psutil.boot_time())
    uptime_seconds = (datetime.now() - boot_time).total_seconds()
    hours, remainder = divmod(int(uptime_seconds), 3600)
    minutes = remainder // 60
    return {
        "os": platform.system(),
        "os_release": platform.release(),
        "hostname": platform.node(),
        "architecture": platform.machine(),
        "python_version": platform.python_version(),
        "boot_time": boot_time.isoformat(),
        "uptime": f"{hours}h {minutes}m",
    }


# ---------------------------------------------------------------------------
# Execução de comando externo (exemplo subprocess)
# ---------------------------------------------------------------------------


def run_shell_check(command: list[str]) -> dict:
    """Executa um comando de shell e captura saída (demonstração de subprocess)."""
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=10,
        )
        return {
            "command": " ".join(command),
            "returncode": result.returncode,
            "stdout": result.stdout.strip()[:500],
            "success": result.returncode == 0,
        }
    except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
        return {"command": " ".join(command), "error": str(exc), "success": False}


# ---------------------------------------------------------------------------
# Construção do relatório final
# ---------------------------------------------------------------------------


def build_report(critical_processes: list[str] | None = None) -> dict:
    """Coleta todas as métricas e retorna o relatório estruturado."""
    critical_processes = critical_processes or CRITICAL_PROCESSES
    ts = datetime.now().isoformat()
    logger.info("Coletando métricas do sistema...")

    cpu = collect_cpu()
    memory = collect_memory()
    disk = collect_disk()
    processes = collect_processes(critical_processes)
    network = collect_network()
    sysinfo = collect_system_info()

    # Determina o status geral
    alerts = [
        cpu["alert"],
        memory["ram"]["alert"],
        any(p["alert"] for p in disk["partitions"]),
        processes["alert"],
    ]
    overall_status = "CRITICAL" if any(alerts) else "OK"

    report = {
        "timestamp": ts,
        "overall_status": overall_status,
        "system_info": sysinfo,
        "cpu": cpu,
        "memory": memory,
        "disk": disk,
        "processes": processes,
        "network": network,
        "thresholds": THRESHOLDS,
        "alerts_active": alerts.count(True),
    }

    logger.info("Status geral: %s | Alertas ativos: %d", overall_status, alerts.count(True))
    return report


# ---------------------------------------------------------------------------
# Persistência e apresentação
# ---------------------------------------------------------------------------


def save_report(report: dict, output_dir: Path) -> Path:
    """Salva o relatório em JSON com timestamp no nome do arquivo."""
    output_dir.mkdir(parents=True, exist_ok=True)
    ts_safe = report["timestamp"].replace(":", "-").replace(".", "-")
    report_path = output_dir / f"health_report_{ts_safe}.json"
    with report_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    logger.info("Relatório salvo: %s", report_path)
    return report_path


def print_dashboard(report: dict) -> None:
    """Exibe um dashboard visual no terminal."""
    cpu = report["cpu"]
    ram = report["memory"]["ram"]
    disks = report["disk"]["partitions"]
    proc = report["processes"]
    net = report["network"]
    sysinfo = report["system_info"]

    status_icon = "✓ OK" if report["overall_status"] == "OK" else "✗ CRITICAL"
    sep = "=" * 60

    print(f"\n{sep}")
    print(f"  MONITOR DE SAÚDE DO SISTEMA  |  {status_icon}")
    print(f"  {report['timestamp']}")
    print(sep)
    print(f"  Host     : {sysinfo['hostname']}  ({sysinfo['os']} {sysinfo['os_release']})")
    print(f"  Uptime   : {sysinfo['uptime']}")
    print(sep)

    # CPU
    cpu_bar = _bar(cpu["global_percent"])
    cpu_alert = " ⚠ ALERTA" if cpu["alert"] else ""
    print(f"  CPU       : {cpu_bar} {cpu['global_percent']:5.1f}%{cpu_alert}")
    print(f"  Cores     : {cpu['logical_cores']} lógicos / {cpu['physical_cores']} físicos")

    # RAM
    ram_bar = _bar(ram["percent"])
    ram_alert = " ⚠ ALERTA" if ram["alert"] else ""
    print(f"  RAM       : {ram_bar} {ram['percent']:5.1f}%{ram_alert}")
    print(f"             {ram['used_gb']}GB / {ram['total_gb']}GB")

    # Disco
    print(f"\n  DISCO:")
    for part in disks:
        disk_bar = _bar(part["percent"])
        disk_alert = " ⚠ ALERTA" if part["alert"] else ""
        print(f"  {part['mountpoint']:<12}: {disk_bar} {part['percent']:5.1f}%{disk_alert}")
        print(f"               {part['used_gb']}GB / {part['total_gb']}GB livres: {part['free_gb']}GB")

    # Rede
    print(f"\n  REDE:")
    print(f"  Enviado  : {net['bytes_sent_mb']} MB  |  Recebido: {net['bytes_recv_mb']} MB")

    # Processos críticos
    print(f"\n  PROCESSOS CRÍTICOS:")
    if proc["critical_missing"]:
        for p in proc["critical_missing"]:
            print(f"  ✗ {p} — NÃO ENCONTRADO")
    else:
        print(f"  Todos os {len(proc['critical_monitored'])} processos críticos estão rodando.")

    print(f"\n  ALERTAS ATIVOS: {report['alerts_active']}")
    print(sep)


def _bar(percent: float, width: int = 20) -> str:
    """Gera uma barra de progresso ASCII."""
    filled = int(percent / 100 * width)
    return "[" + "#" * filled + "-" * (width - filled) + "]"


# ---------------------------------------------------------------------------
# Ponto de entrada
# ---------------------------------------------------------------------------


def main() -> None:
    import argparse

    base = Path(__file__).parent.parent
    parser = argparse.ArgumentParser(
        description="Monitor de saúde do sistema com alertas e relatório JSON."
    )
    parser.add_argument(
        "--output-dir",
        default=str(base / "output"),
        help="Diretório para salvar os relatórios JSON",
    )
    parser.add_argument(
        "--processes",
        nargs="*",
        default=CRITICAL_PROCESSES,
        help="Lista de processos críticos a monitorar",
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Exibe o dashboard sem salvar o arquivo JSON",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Imprime o JSON completo na saída padrão",
    )
    args = parser.parse_args()

    start = time.perf_counter()
    report = build_report(critical_processes=args.processes)

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print_dashboard(report)

    if not args.no_save:
        save_report(report, Path(args.output_dir))

    elapsed = time.perf_counter() - start
    logger.info("Verificação concluída em %.3fs.", elapsed)

    # Sai com código 1 se houver alertas críticos
    if report["overall_status"] == "CRITICAL":
        sys.exit(1)


if __name__ == "__main__":
    main()
