#!/usr/bin/env bash
# =============================================================================
# backup_automation.sh - Automação Profissional de Backup
# Comprime diretórios, cria backups versionados e remove arquivos antigos.
# =============================================================================
# USO:
#   ./backup_automation.sh [--dry-run]
#
# EXEMPLOS DE CRON:
#   # Diário às 02:00
#   0 2 * * * /opt/automation-suite/scripts/backup_automation.sh >> /opt/automation-suite/logs/cron_backup.log 2>&1
#
#   # Semanal (domingo, 03:30)
#   30 3 * * 0 /opt/automation-suite/scripts/backup_automation.sh --dry-run
#
# COMO RESTAURAR:
#   tar -xzf /backups/backup_meudir_20240101_143000.tar.gz -C /destino/
# =============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# Configurações — ajuste conforme necessário
# ---------------------------------------------------------------------------

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly BASE_DIR="$(dirname "$SCRIPT_DIR")"

SOURCE_DIRS=(
    "$BASE_DIR/input"
    "$BASE_DIR/output"
)

BACKUP_DEST="$BASE_DIR/backups"
LOG_FILE="$BASE_DIR/logs/backup_automation.log"
MAX_BACKUPS=7          # Máximo de backups por diretório-fonte antes de deletar os mais antigos
COMPRESSION="gz"       # gz | bz2 | xz
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
DRY_RUN=false

# ---------------------------------------------------------------------------
# Funções auxiliares
# ---------------------------------------------------------------------------

log() {
    local level="$1"
    local msg="$2"
    local ts
    ts="$(date '+%Y-%m-%d %H:%M:%S')"
    printf "%s | %-8s | %s\n" "$ts" "$level" "$msg" | tee -a "$LOG_FILE"
}

log_info()  { log "INFO    " "$1"; }
log_warn()  { log "WARNING " "$1"; }
log_error() { log "ERROR   " "$1"; }
log_ok()    { log "OK      " "$1"; }

die() {
    log_error "$1"
    exit 1
}

ensure_dir() {
    local dir="$1"
    if [[ "$DRY_RUN" == false ]]; then
        mkdir -p "$dir" || die "Falha ao criar diretório: $dir"
    else
        log_info "[DRY-RUN] Criaria diretório: $dir"
    fi
}

# ---------------------------------------------------------------------------
# Verificações de pré-requisitos
# ---------------------------------------------------------------------------

check_dependencies() {
    local deps=("tar" "gzip" "find" "date" "du")
    for dep in "${deps[@]}"; do
        command -v "$dep" &>/dev/null || die "Dependência não encontrada: $dep"
    done
    log_info "Dependências verificadas com sucesso."
}

check_disk_space() {
    local source="$1"
    local dest="$2"

    local src_size_kb
    src_size_kb=$(du -sk "$source" 2>/dev/null | cut -f1 || echo 0)

    local dest_avail_kb
    dest_avail_kb=$(df -k "$dest" 2>/dev/null | awk 'NR==2 {print $4}' || echo 999999999)

    if (( src_size_kb > dest_avail_kb )); then
        log_warn "Espaço insuficiente em '$dest'. Necessário: ${src_size_kb}KB | Disponível: ${dest_avail_kb}KB"
        return 1
    fi
    return 0
}

# ---------------------------------------------------------------------------
# Criação do backup
# ---------------------------------------------------------------------------

create_backup() {
    local source="$1"
    local dest_dir="$2"

    if [[ ! -d "$source" ]]; then
        log_warn "Fonte não existe ou não é um diretório: $source — pulando."
        return
    fi

    local dir_name
    dir_name="$(basename "$source")"
    local archive_name="backup_${dir_name}_${TIMESTAMP}.tar.${COMPRESSION}"
    local archive_path="${dest_dir}/${archive_name}"

    log_info "Iniciando backup: '$source' → '$archive_path'"

    if [[ "$DRY_RUN" == true ]]; then
        log_info "[DRY-RUN] Executaria: tar -czf '$archive_path' -C '$(dirname "$source")' '$dir_name'"
        return
    fi

    check_disk_space "$source" "$dest_dir" || {
        log_error "Backup de '$source' abortado por falta de espaço."
        return
    }

    local tar_flag
    case "$COMPRESSION" in
        gz)  tar_flag="z" ;;
        bz2) tar_flag="j" ;;
        xz)  tar_flag="J" ;;
        *)   die "Compressão inválida: $COMPRESSION" ;;
    esac

    if tar "-c${tar_flag}f" "$archive_path" -C "$(dirname "$source")" "$dir_name" 2>>"$LOG_FILE"; then
        local size
        size=$(du -sh "$archive_path" | cut -f1)
        log_ok "Backup criado com sucesso: $archive_name (${size})"
    else
        log_error "Falha ao criar backup de: $source"
        rm -f "$archive_path"
    fi
}

# ---------------------------------------------------------------------------
# Rotação de backups antigos
# ---------------------------------------------------------------------------

rotate_backups() {
    local source_name="$1"
    local dest_dir="$2"

    local count
    count=$(find "$dest_dir" -maxdepth 1 -name "backup_${source_name}_*.tar.*" | wc -l)

    if (( count <= MAX_BACKUPS )); then
        return
    fi

    local to_delete=$(( count - MAX_BACKUPS ))
    log_info "Rotacionando backups antigos de '$source_name' (removendo $to_delete)..."

    mapfile -t old_files < <(
        find "$dest_dir" -maxdepth 1 -name "backup_${source_name}_*.tar.*" \
        | sort | head -n "$to_delete"
    )

    for f in "${old_files[@]}"; do
        if [[ "$DRY_RUN" == true ]]; then
            log_info "[DRY-RUN] Removeria: $(basename "$f")"
        else
            rm -f "$f"
            log_info "Backup antigo removido: $(basename "$f")"
        fi
    done
}

# ---------------------------------------------------------------------------
# Verificação de integridade
# ---------------------------------------------------------------------------

verify_backup() {
    local archive="$1"

    if [[ "$DRY_RUN" == true ]]; then
        return
    fi

    if tar -tf "$archive" &>/dev/null; then
        log_ok "Integridade verificada: $(basename "$archive")"
    else
        log_error "Falha na verificação de integridade: $(basename "$archive")"
    fi
}

# ---------------------------------------------------------------------------
# Ponto de entrada
# ---------------------------------------------------------------------------

main() {
    # Processar argumentos
    for arg in "$@"; do
        case "$arg" in
            --dry-run) DRY_RUN=true ;;
            --help|-h)
                echo "Uso: $(basename "$0") [--dry-run]"
                echo "  --dry-run  Simula a execução sem criar arquivos"
                exit 0
                ;;
            *) die "Argumento desconhecido: $arg" ;;
        esac
    done

    # Criar diretórios necessários
    ensure_dir "$BACKUP_DEST"
    ensure_dir "$(dirname "$LOG_FILE")"

    local mode_label=""
    [[ "$DRY_RUN" == true ]] && mode_label=" [DRY-RUN]"

    log_info "=============================================="
    log_info "Backup Automation v1.0${mode_label}"
    log_info "Timestamp : $TIMESTAMP"
    log_info "Destino   : $BACKUP_DEST"
    log_info "Máx/dir   : $MAX_BACKUPS backups"
    log_info "=============================================="

    check_dependencies

    local success=0
    local failure=0

    for source in "${SOURCE_DIRS[@]}"; do
        local dir_name
        dir_name="$(basename "$source")"

        create_backup "$source" "$BACKUP_DEST"

        # Verificar integridade do arquivo mais recente
        local latest
        latest=$(find "$BACKUP_DEST" -maxdepth 1 -name "backup_${dir_name}_*.tar.*" \
                 | sort | tail -n 1)
        if [[ -n "$latest" && "$DRY_RUN" == false ]]; then
            verify_backup "$latest" && (( success++ )) || (( failure++ ))
        fi

        rotate_backups "$dir_name" "$BACKUP_DEST"
    done

    log_info "----------------------------------------------"
    log_info "Resumo: ${success} backup(s) OK | ${failure} falha(s)"
    log_info "=============================================="
}

main "$@"
