#!/usr/bin/env python3
"""
launcher.py - Suite de Automação de Tarefas Operacionais
Menu interativo para executar todos os scripts da suite.
"""

import os
import subprocess
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

# Resolve o diretório base mesmo quando rodando como .exe (PyInstaller)
if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).parent

SCRIPTS_DIR = BASE_DIR / "scripts"

MENU = """
╔══════════════════════════════════════════════════════════╗
║       SUITE DE AUTOMAÇÃO DE TAREFAS OPERACIONAIS        ║
╠══════════════════════════════════════════════════════════╣
║                                                          ║
║  [1] Organizador de Arquivos                             ║
║      Organiza arquivos por extensão com anti-duplicata   ║
║                                                          ║
║  [2] Gerador de Relatórios CSV/Excel                     ║
║      Merge, limpeza e exportação formatada               ║
║                                                          ║
║  [3] Formatador de Dados em Massa                        ║
║      Padroniza nomes, emails, telefones e datas          ║
║                                                          ║
║  [4] Monitor de Saúde do Sistema                         ║
║      CPU, RAM, disco e processos com alertas             ║
║                                                          ║
║  [5] Backup Automático (requer Bash/WSL)                 ║
║      Backup comprimido e versionado com rotação          ║
║                                                          ║
║  [0] Sair                                                ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
"""


def clear():
    os.system("cls" if os.name == "nt" else "clear")


def pause():
    input("\n  Pressione ENTER para voltar ao menu...")


def header(title: str):
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}\n")


def run_python_script(script_name: str, extra_args: list[str] | None = None):
    """Executa um script Python da pasta scripts/ com o mesmo interpretador."""
    script_path = SCRIPTS_DIR / script_name
    if not script_path.exists():
        print(f"\n  ERRO: script não encontrado em {script_path}")
        pause()
        return

    cmd = [sys.executable, str(script_path)] + (extra_args or [])
    print(f"  Executando: {script_name}\n")
    try:
        subprocess.run(cmd, check=False)
    except KeyboardInterrupt:
        print("\n  Execução interrompida pelo usuário.")
    pause()


# ---------------------------------------------------------------------------
# Opções do menu
# ---------------------------------------------------------------------------


def menu_organizer():
    clear()
    header("ORGANIZADOR DE ARQUIVOS")
    print("  Diretório padrão: input/")
    print("  Os arquivos serão movidos para subpastas por extensão.\n")
    modo = input("  Executar em [1] modo real  ou  [2] dry-run (simulação)? ").strip()
    args = ["--dry-run"] if modo == "2" else []
    run_python_script("organize_files.py", args)


def menu_report():
    clear()
    header("GERADOR DE RELATÓRIOS")
    print("  Lê todos os CSVs de input/sample_csvs/")
    print("  Gera relatório em output/relatorio_consolidado.csv e .xlsx\n")
    run_python_script("report_generator.py")


def menu_formatter():
    clear()
    header("FORMATADOR DE DADOS EM MASSA")
    print("  Arquivo de entrada: input/raw_data.csv")
    print("  Colunas: nome, email, telefone, data_nascimento\n")
    run_python_script("bulk_data_formatter.py")


def menu_health():
    clear()
    header("MONITOR DE SAÚDE DO SISTEMA")
    proc_input = input(
        "  Processos críticos a monitorar (ENTER para padrão 'python'): "
    ).strip()
    procs = proc_input.split() if proc_input else ["python"]
    args = ["--processes"] + procs
    run_python_script("system_health_check.py", args)


def menu_backup():
    clear()
    header("BACKUP AUTOMÁTICO (BASH)")
    print("  Este script requer Bash (Linux, macOS ou WSL no Windows).\n")

    bash_path = None
    for candidate in ["bash", r"C:\Windows\System32\bash.exe", r"C:\Program Files\Git\bin\bash.exe"]:
        try:
            result = subprocess.run([candidate, "--version"], capture_output=True, timeout=3)
            if result.returncode == 0:
                bash_path = candidate
                break
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue

    if not bash_path:
        print("  Bash não encontrado. Instale o WSL ou Git for Windows.")
        print("  Comando manual: bash scripts/backup_automation.sh --dry-run")
        pause()
        return

    script_path = SCRIPTS_DIR / "backup_automation.sh"
    modo = input("  Executar em [1] modo real  ou  [2] dry-run (simulação)? ").strip()
    args = [bash_path, str(script_path)]
    if modo == "2":
        args.append("--dry-run")

    print(f"\n  Executando backup via: {bash_path}\n")
    try:
        subprocess.run(args, check=False)
    except KeyboardInterrupt:
        print("\n  Execução interrompida.")
    pause()


# ---------------------------------------------------------------------------
# Loop principal
# ---------------------------------------------------------------------------


def main():
    actions = {
        "1": menu_organizer,
        "2": menu_report,
        "3": menu_formatter,
        "4": menu_health,
        "5": menu_backup,
    }

    while True:
        clear()
        print(MENU)
        choice = input("  Escolha uma opção: ").strip()

        if choice == "0":
            clear()
            print("\n  Encerrando. Até mais!\n")
            time.sleep(1)
            break
        elif choice in actions:
            actions[choice]()
        else:
            print("\n  Opção inválida. Tente novamente.")
            time.sleep(1)


if __name__ == "__main__":
    main()
