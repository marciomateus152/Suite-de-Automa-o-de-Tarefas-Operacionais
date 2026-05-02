# Suite de Automação de Tarefas Operacionais

Coleção de scripts Python e Bash para automatizar tarefas repetitivas de manipulação de arquivos, processamento de dados e monitoramento de sistemas.

---

## Scripts

| # | Arquivo | O que faz |
|---|---|---|
| 1 | `organize_files.py` | Organiza arquivos por extensão em subpastas, detecta duplicatas por hash MD5 |
| 2 | `report_generator.py` | Consolida múltiplos CSVs, remove duplicatas e exporta Excel formatado |
| 3 | `bulk_data_formatter.py` | Padroniza nomes, emails, telefones e datas em grandes volumes de dados |
| 4 | `backup_automation.sh` | Cria backups comprimidos e versionados com rotação automática |
| 5 | `system_health_check.py` | Monitora CPU, RAM, disco e processos, gera alertas e relatório JSON |

---

## Estrutura

```
automation-suite/
├── scripts/
│   ├── organize_files.py
│   ├── report_generator.py
│   ├── bulk_data_formatter.py
│   ├── backup_automation.sh
│   └── system_health_check.py
├── input/
│   ├── sample_csvs/        ← CSVs de exemplo para o gerador de relatórios
│   └── raw_data.csv        ← Dados brutos para o formatador
├── output/                 ← Relatórios e arquivos gerados
├── logs/                   ← Logs de execução
├── backups/                ← Backups comprimidos
├── launcher.py             ← Menu interativo para rodar qualquer script
└── requirements.txt
```

---

## Instalação

**Pré-requisitos:** Python 3.12+ · Bash (Linux, macOS ou WSL)

```bash
git clone https://github.com/marciomateus152/Suite-de-Automa-o-de-Tarefas-Operacionais.git
cd Suite-de-Automa-o-de-Tarefas-Operacionais

python -m venv venv
source venv/bin/activate        # Linux/macOS
# .\venv\Scripts\activate       # Windows

pip install -r requirements.txt
chmod +x scripts/backup_automation.sh
```

---

## Como usar

### Menu interativo (recomendado)

```bash
python launcher.py
```

```
╔══════════════════════════════════════════════════════════╗
║       SUITE DE AUTOMAÇÃO DE TAREFAS OPERACIONAIS        ║
╠══════════════════════════════════════════════════════════╣
║  [1] Organizador de Arquivos                             ║
║  [2] Gerador de Relatórios CSV/Excel                     ║
║  [3] Formatador de Dados em Massa                        ║
║  [4] Monitor de Saúde do Sistema                         ║
║  [5] Backup Automático (requer Bash/WSL)                 ║
║  [0] Sair                                                ║
╚══════════════════════════════════════════════════════════╝
```

### Executar scripts individualmente

```bash
python scripts/organize_files.py
python scripts/report_generator.py
python scripts/bulk_data_formatter.py
python scripts/system_health_check.py
bash   scripts/backup_automation.sh
```

Todos os scripts aceitam `--help` para ver as opções disponíveis.

---

## Scripts em detalhe

### 1. Organizador de Arquivos

Varre um diretório e move cada arquivo para a subpasta correta com base na extensão. Antes de mover, calcula o hash MD5 para evitar duplicatas.

**Categorias:** `images` · `documents` · `videos` · `spreadsheets` · `audio` · `code` · `archives` · `others`

```bash
python scripts/organize_files.py                        # organiza input/
python scripts/organize_files.py /outro/diretorio       # diretório específico
python scripts/organize_files.py --dry-run              # simula sem mover nada
```

```
2026-05-02 15:55:10 | INFO    | Arquivos encontrados: 47
2026-05-02 15:55:10 | INFO    | Movido: 'relatorio.pdf' → documents/
2026-05-02 15:55:10 | WARNING | Duplicata detectada: 'relatorio_v2.pdf'. Ignorando.

  Arquivos movidos    : 45
  Duplicatas saltadas : 2
  Tempo de execução   : 0.847s
```

---

### 2. Gerador de Relatórios CSV/Excel

Lê todos os arquivos `.csv` de um diretório, combina em um único DataFrame, remove duplicatas e linhas vazias, e exporta dois arquivos: um CSV limpo e um Excel formatado.

**O Excel gerado tem:** cabeçalho colorido · linhas alternadas · colunas ajustadas automaticamente · filtros · painel congelado

```bash
python scripts/report_generator.py
python scripts/report_generator.py --input-dir dados/ --report-name vendas_q1
python scripts/report_generator.py --encoding latin-1
```

```
  Linhas iniciais     : 22
  Duplicatas removidas: 1
  Linhas no relatório : 21
  Tempo               : 0.074s

  → output/relatorio_consolidado.csv
  → output/relatorio_consolidado.xlsx
```

---

### 3. Formatador de Dados em Massa

Lê um CSV com dados inconsistentes e aplica um pipeline de limpeza coluna por coluna. Linhas completamente vazias são isoladas em um relatório separado.

| Campo | Antes | Depois |
|---|---|---|
| Nome | `ana  SILVA` | `Ana Silva` |
| Email | `EMAIL_INVALIDO` | *(vazio)* |
| Telefone | `11987654321` | `(11) 98765-4321` |
| Data | `1990-03-15` | `15/03/1990` |

```bash
python scripts/bulk_data_formatter.py
python scripts/bulk_data_formatter.py --input meus_dados.csv \
  --col-map '{"nome":"name","email":"email","telefone":"phone","data":"date"}'
```

**Tipos suportados no `--col-map`:** `name` · `email` · `phone` · `date`

```
  Registros carregados  : 21
  Linhas corrompidas    : 2   → output/inconsistency_report.csv
  Nomes padronizados    : 19
  Emails inválidos      : 3
  Telefones formatados  : 19
  Datas normalizadas    : 10
```

---

### 4. Backup Automático

Comprime cada diretório configurado em `.tar.gz` com timestamp, verifica a integridade do arquivo gerado e apaga os backups mais antigos automaticamente.

```bash
bash scripts/backup_automation.sh            # executa o backup
bash scripts/backup_automation.sh --dry-run  # simula sem criar arquivos
```

```
2026-05-02 02:00:01 | INFO | Iniciando backup: 'input' → backups/backup_input_20260502_020001.tar.gz
2026-05-02 02:00:03 | OK   | Backup criado: backup_input_20260502_020001.tar.gz (2.3M)
2026-05-02 02:00:03 | OK   | Integridade verificada.
2026-05-02 02:00:03 | INFO | Resumo: 2 OK | 0 falhas
```

**Como restaurar:**
```bash
tar -xzf backups/backup_input_20260502_020001.tar.gz -C /destino/
```

**Agendamento com cron:**
```bash
# Backup diário às 02:00
0 2 * * * /caminho/scripts/backup_automation.sh >> /caminho/logs/cron.log 2>&1
```

**Configurações** (no topo do script):
```bash
SOURCE_DIRS=("$BASE_DIR/input" "$BASE_DIR/output")  # diretórios a copiar
MAX_BACKUPS=7                                         # quantos manter por pasta
COMPRESSION="gz"                                      # gz | bz2 | xz
```

---

### 5. Monitor de Saúde do Sistema

Coleta métricas de CPU, memória, disco e processos em tempo real. Exibe um dashboard no terminal, dispara alertas quando os limiares são ultrapassados e salva um relatório JSON em `output/`.

```bash
python scripts/system_health_check.py
python scripts/system_health_check.py --processes nginx postgres redis
python scripts/system_health_check.py --no-save   # sem salvar JSON
python scripts/system_health_check.py --json      # saída JSON pura
```

```
  MONITOR DE SAÚDE DO SISTEMA  |  ✓ OK
  Host   : servidor-prod (Linux 5.15.0) — Uptime: 12h 43m

  CPU    : [####----------------]  18.5%
  RAM    : [########------------]  42.3%   6.8GB / 16.0GB

  DISCO:
  /      : [##########----------]  51.2%   102GB / 200GB

  ALERTAS ATIVOS: 0
```

**Limiares de alerta:**

| Métrica | Limite |
|---|---|
| CPU | > 90% |
| RAM | > 80% |
| Disco | > 85% |
| Processo ausente | qualquer |

> O script retorna exit code `1` quando há alertas ativos, tornando-o compatível com pipelines de CI/CD e scripts de monitoramento.

---

## Logs

Cada script grava um log em `logs/` com o formato:

```
2026-05-02 14:32:01 | INFO     | Mensagem
2026-05-02 14:32:02 | WARNING  | Aviso
2026-05-02 14:32:03 | ERROR    | Erro tratado
2026-05-02 14:32:04 | CRITICAL | Erro fatal
```

---

## Stack

`Python 3.12` · `pandas` · `openpyxl` · `psutil` · `pathlib` · `subprocess` · `Bash`

---

## Licença

MIT
