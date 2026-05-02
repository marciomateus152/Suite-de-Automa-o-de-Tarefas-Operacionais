#!/usr/bin/env python3
"""
organize_files.py - Organizador Automático de Arquivos
Monitora uma pasta e organiza arquivos por extensão em subdiretórios.
"""

import hashlib
import logging
import shutil
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

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
        logging.FileHandler(LOG_DIR / "organize_files.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Mapeamento de extensões → subpastas
# ---------------------------------------------------------------------------

EXTENSION_MAP: dict[str, str] = {
    # Imagens
    ".jpg": "images", ".jpeg": "images", ".png": "images",
    ".gif": "images", ".bmp": "images", ".svg": "images",
    ".webp": "images", ".ico": "images", ".tiff": "images",
    # Documentos
    ".pdf": "documents", ".doc": "documents", ".docx": "documents",
    ".txt": "documents", ".odt": "documents", ".rtf": "documents",
    ".md": "documents", ".pptx": "documents", ".ppt": "documents",
    # Vídeos
    ".mp4": "videos", ".avi": "videos", ".mkv": "videos",
    ".mov": "videos", ".wmv": "videos", ".flv": "videos",
    ".webm": "videos", ".m4v": "videos",
    # Planilhas
    ".xlsx": "spreadsheets", ".xls": "spreadsheets",
    ".csv": "spreadsheets", ".ods": "spreadsheets",
    # Áudio
    ".mp3": "audio", ".wav": "audio", ".flac": "audio",
    ".aac": "audio", ".ogg": "audio", ".m4a": "audio",
    # Código
    ".py": "code", ".js": "code", ".ts": "code",
    ".sh": "code", ".json": "code", ".yaml": "code",
    ".yml": "code", ".xml": "code", ".html": "code",
    ".css": "code", ".sql": "code",
    # Comprimidos
    ".zip": "archives", ".tar": "archives", ".gz": "archives",
    ".rar": "archives", ".7z": "archives",
}

# ---------------------------------------------------------------------------
# Utilitários
# ---------------------------------------------------------------------------


def compute_md5(path: Path, chunk_size: int = 65536) -> str:
    """Calcula o hash MD5 de um arquivo para detecção de duplicatas."""
    hasher = hashlib.md5()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def unique_destination(dest: Path) -> Path:
    """Retorna um caminho único adicionando sufixo numérico se necessário."""
    if not dest.exists():
        return dest
    stem = dest.stem
    suffix = dest.suffix
    parent = dest.parent
    counter = 1
    while True:
        candidate = parent / f"{stem}_{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def resolve_category(extension: str) -> str:
    """Resolve a categoria de destino com base na extensão do arquivo."""
    return EXTENSION_MAP.get(extension.lower(), "others")


# ---------------------------------------------------------------------------
# Lógica principal
# ---------------------------------------------------------------------------


def organize_directory(source_dir: Path, dry_run: bool = False) -> dict:
    """
    Organiza todos os arquivos de source_dir em subdiretórios por categoria.

    Args:
        source_dir: Diretório a ser organizado.
        dry_run: Se True, apenas simula as operações sem mover arquivos.

    Returns:
        Dicionário com estatísticas da execução.
    """
    if not source_dir.exists():
        raise FileNotFoundError(f"Diretório não encontrado: {source_dir}")
    if not source_dir.is_dir():
        raise NotADirectoryError(f"Caminho não é um diretório: {source_dir}")

    start_time = time.perf_counter()
    mode_label = "[DRY-RUN] " if dry_run else ""
    logger.info("%sIniciando organização em: %s", mode_label, source_dir.resolve())

    stats = {
        "moved": 0,
        "skipped_dirs": 0,
        "duplicates": 0,
        "errors": 0,
        "by_category": {},
        "error_list": [],
    }

    # Índice de hashes para detecção de duplicatas nesta execução
    seen_hashes: dict[str, Path] = {}

    files = [f for f in source_dir.iterdir() if f.is_file()]
    logger.info("Arquivos encontrados: %d", len(files))

    for file_path in files:
        try:
            file_hash = compute_md5(file_path)

            if file_hash in seen_hashes:
                original = seen_hashes[file_hash]
                logger.warning(
                    "Duplicata detectada: '%s' é idêntico a '%s'. Ignorando.",
                    file_path.name,
                    original.name,
                )
                stats["duplicates"] += 1
                continue

            seen_hashes[file_hash] = file_path
            category = resolve_category(file_path.suffix)
            dest_dir = source_dir / category

            if not dry_run:
                dest_dir.mkdir(exist_ok=True)

            dest_path = unique_destination(dest_dir / file_path.name)

            if dry_run:
                logger.info("[DRY-RUN] Moveria '%s' → %s/", file_path.name, category)
            else:
                shutil.move(str(file_path), str(dest_path))
                logger.info("Movido: '%s' → %s/", file_path.name, category)

            stats["moved"] += 1
            stats["by_category"][category] = stats["by_category"].get(category, 0) + 1

        except PermissionError as exc:
            msg = f"Sem permissão para mover '{file_path.name}': {exc}"
            logger.error(msg)
            stats["errors"] += 1
            stats["error_list"].append(msg)
        except OSError as exc:
            msg = f"Erro de SO ao processar '{file_path.name}': {exc}"
            logger.error(msg)
            stats["errors"] += 1
            stats["error_list"].append(msg)

    elapsed = time.perf_counter() - start_time
    stats["elapsed_seconds"] = round(elapsed, 3)
    return stats


def print_report(stats: dict) -> None:
    """Exibe o relatório final de execução no terminal."""
    sep = "=" * 55
    print(f"\n{sep}")
    print("  RELATÓRIO DE ORGANIZAÇÃO DE ARQUIVOS")
    print(sep)
    print(f"  Arquivos movidos    : {stats['moved']}")
    print(f"  Duplicatas saltadas : {stats['duplicates']}")
    print(f"  Erros               : {stats['errors']}")
    print(f"  Tempo de execução   : {stats['elapsed_seconds']}s")
    if stats["by_category"]:
        print(f"\n  Distribuição por categoria:")
        for cat, count in sorted(stats["by_category"].items()):
            print(f"    {cat:<15} → {count} arquivo(s)")
    if stats["error_list"]:
        print(f"\n  Erros encontrados:")
        for err in stats["error_list"]:
            print(f"    ✗ {err}")
    print(sep)


# ---------------------------------------------------------------------------
# Ponto de entrada
# ---------------------------------------------------------------------------


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Organizador automático de arquivos por extensão."
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default=str(Path(__file__).parent.parent / "input"),
        help="Diretório a organizar (padrão: ../input)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simula a execução sem mover arquivos",
    )
    args = parser.parse_args()

    source = Path(args.directory).resolve()
    try:
        stats = organize_directory(source, dry_run=args.dry_run)
        print_report(stats)
        logger.info("Organização concluída em %.3fs.", stats["elapsed_seconds"])
    except (FileNotFoundError, NotADirectoryError) as exc:
        logger.critical("Erro crítico: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
