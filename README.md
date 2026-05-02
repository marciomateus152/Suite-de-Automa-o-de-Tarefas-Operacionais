# Suite de Automação de Tarefas Operacionais

Pipeline de automação Python/Bash para eliminação de tarefas repetitivas de manipulação de arquivos, processamento de dados e monitoramento de infraestrutura.

---

## Visão Geral

| Script | Tecnologias | Finalidade |
|---|---|---|
| `organize_files.py` | Python, pathlib | Organiza arquivos por extensão com detecção de duplicatas |
| `report_generator.py` | pandas, openpyxl | Merge de CSVs + relatório Excel formatado |
| `bulk_data_formatter.py` | pandas, regex | Padronização em massa de dados (nomes, datas, telefones, emails) |
| `backup_automation.sh` | Bash, tar, cron | Backup comprimido e versionado de diretórios |
| `system_health_check.py` | psutil, subprocess | Monitor de CPU, RAM, disco e processos com alertas |

---

## Estrutura do Projeto

```
automation-suite/
├── scripts/
│   ├── organize_files.py        # Script 1 — Organizador de Arquivos
│   ├── report_generator.py      # Script 2 — Gerador de Relatórios
│   ├── bulk_data_formatter.py   # Script 3 — Formatador em Massa
│   ├── backup_automation.sh     # Script 4 — Backup Automatizado
│   └── system_health_check.py   # Script 5 — Monitor de Saúde
│
├── input/
│   ├── sample_csvs/             # CSVs de exemplo para o gerador de relatórios
│   └── raw_data.csv             # Dados brutos para o formatador
│
├── output/                      # Relatórios e dados processados gerados
├── logs/                        # Logs de execução de todos os scripts
├── backups/                     # Backups comprimidos gerados pelo script Bash
│
├── requirements.txt
├── .gitignore
└── README.md
```

---

## Pré-requisitos

- Python 3.12+
- pip
- Bash (Linux/macOS/WSL)

---

## Instalação

```bash
git clone https://github.com/seu-usuario/automation-suite.git
cd automation-suite
python -m venv venv
source venv/bin/activate        # Linux/macOS
# .\venv\Scripts\activate       # Windows
pip install -r requirements.txt
chmod +x scripts/backup_automation.sh
```

---

## Scripts — Uso Detalhado

### 1. Organizador Automático de Arquivos

Monitora a pasta `input/` e organiza arquivos em subdiretórios por categoria.

**Categorias suportadas:** images, documents, videos, spreadsheets, audio, code, archives, others

```bash
# Organizar a pasta padrão (input/)
python scripts/organize_files.py

# Organizar uma pasta específica
python scripts/organize_files.py /caminho/para/pasta

# Simular sem mover arquivos (dry-run)
python scripts/organize_files.py --dry-run
```

**Output esperado:**
```
2024-01-15 14:32:01 | INFO     | Iniciando organização em: /projeto/input
2024-01-15 14:32:01 | INFO     | Arquivos encontrados: 47
2024-01-15 14:32:01 | INFO     | Movido: 'relatorio.pdf' → documents/
2024-01-15 14:32:01 | INFO     | Movido: 'foto_reuniao.jpg' → images/
2024-01-15 14:32:01 | WARNING  | Duplicata detectada: 'backup_relatorio.pdf' é idêntico a 'relatorio.pdf'. Ignorando.

=======================================================
  RELATÓRIO DE ORGANIZAÇÃO DE ARQUIVOS
=======================================================
  Arquivos movidos    : 45
  Duplicatas saltadas : 2
  Erros               : 0
  Tempo de execução   : 0.847s

  Distribuição por categoria:
    documents       → 18 arquivo(s)
    images          → 12 arquivo(s)
    spreadsheets    → 8 arquivo(s)
    videos          → 5 arquivo(s)
    others          → 2 arquivo(s)
=======================================================
```

---

### 2. Gerador de Relatórios CSV/Excel

Lê todos os CSVs de um diretório, realiza merge, limpeza e exporta relatório consolidado em CSV e Excel formatado.

```bash
# Usando o diretório padrão (input/sample_csvs/)
python scripts/report_generator.py

# Especificando diretórios e nome
python scripts/report_generator.py \
  --input-dir input/sample_csvs \
  --output-dir output \
  --report-name relatorio_q1_2024

# Com encoding diferente
python scripts/report_generator.py --encoding latin-1
```

**Output esperado:**
```
2024-01-15 14:33:10 | INFO     | CSV carregado: 'vendas_janeiro.csv' (10 linhas)
2024-01-15 14:33:10 | INFO     | CSV carregado: 'vendas_fevereiro.csv' (10 linhas)
2024-01-15 14:33:10 | INFO     | Total combinado antes da limpeza: 20 linhas.
2024-01-15 14:33:10 | INFO     | Duplicatas removidas: 1
2024-01-15 14:33:10 | INFO     | Excel formatado exportado: output/relatorio_consolidado.xlsx

=======================================================
  RELATÓRIO DE GERAÇÃO — MÉTRICAS
=======================================================
  Linhas iniciais          : 21
  Colunas vazias removidas : 0
  Linhas em branco         : 1
  Duplicatas removidas     : 1
  Linhas no relatório final: 19
  Colunas finais           : 8
  Tempo de processamento   : 1.234s

  Arquivos gerados:
    CSV  → output/relatorio_consolidado.csv
    XLSX → output/relatorio_consolidado.xlsx
=======================================================
```

**O Excel gerado inclui:**
- Cabeçalho com fundo azul escuro e texto branco bold
- Linhas alternadas em azul claro (zebra striping)
- Ajuste automático de largura de colunas
- Filtros automáticos na linha de cabeçalho
- Painel congelado no cabeçalho

---

### 3. Formatador de Dados em Massa

Pipeline de padronização que processa milhares de registros: nomes em Title Case, emails lowercase validados, telefones no padrão brasileiro, datas em formato único.

```bash
# Usando o arquivo padrão (input/raw_data.csv)
python scripts/bulk_data_formatter.py

# Especificando arquivo e mapeamento de colunas
python scripts/bulk_data_formatter.py \
  --input input/raw_data.csv \
  --output-dir output \
  --col-map '{"nome":"name","email":"email","telefone":"phone","data_nascimento":"date"}'

# Com encoding latin-1
python scripts/bulk_data_formatter.py --encoding latin-1
```

**Tipos de coluna suportados:** `name` | `email` | `phone` | `date`

**Output esperado:**
```
2024-01-15 14:34:05 | INFO     | Carregando: input/raw_data.csv
2024-01-15 14:34:05 | INFO     | Registros carregados: 20
2024-01-15 14:34:05 | INFO     | Linhas corrompidas identificadas: 2
2024-01-15 14:34:05 | INFO     | Coluna 'nome' (name): 14 registros padronizados.
2024-01-15 14:34:05 | INFO     | Coluna 'email' (email): 18 registros padronizados.
2024-01-15 14:34:05 | WARNING  | Emails inválidos (campo zerado): 3

=======================================================
  RELATÓRIO DE FORMATAÇÃO EM MASSA
=======================================================
  Total de registros        : 20
  Linhas corrompidas        : 2
  Linhas processadas        : 18
  Nomes padronizados        : 14
  Emails padronizados       : 18
  Emails inválidos (zerados): 3
  Telefones padronizados    : 17
  Datas padronizadas        : 18
  Tempo de processamento    : 0.312s

  Arquivo limpo exportado   : output/formatted_raw_data.csv
=======================================================
```

**Exemplos de transformação:**

| Campo | Antes | Depois |
|---|---|---|
| Nome | `ana  SILVA` | `Ana Silva` |
| Email | `EMAIL_INVALIDO` | *(vazio — inválido)* |
| Telefone | `11987654321` | `(11) 98765-4321` |
| Data | `1990-03-15` | `15/03/1990` |

---

### 4. Automação de Backup com Bash

Script Bash profissional para backup comprimido, versionado e com rotação automática.

```bash
# Executar backup real
./scripts/backup_automation.sh

# Simular execução (dry-run)
./scripts/backup_automation.sh --dry-run

# Ajuda
./scripts/backup_automation.sh --help
```

**Output esperado:**
```
2024-01-15 02:00:01 | OK       | Dependências verificadas com sucesso.
2024-01-15 02:00:01 | INFO     | Iniciando backup: '/projeto/input' → 'backups/backup_input_20240115_020001.tar.gz'
2024-01-15 02:00:03 | OK       | Backup criado com sucesso: backup_input_20240115_020001.tar.gz (2.3M)
2024-01-15 02:00:03 | OK       | Integridade verificada: backup_input_20240115_020001.tar.gz
2024-01-15 02:00:03 | INFO     | Rotacionando backups antigos de 'input' (removendo 1)...
2024-01-15 02:00:03 | INFO     | Backup antigo removido: backup_input_20240108_020001.tar.gz
2024-01-15 02:00:03 | INFO     | Resumo: 2 backup(s) OK | 0 falha(s)
```

**Como restaurar um backup:**
```bash
# Listar conteúdo do backup sem extrair
tar -tzf backups/backup_input_20240115_020001.tar.gz

# Restaurar no diretório original
tar -xzf backups/backup_input_20240115_020001.tar.gz -C /destino/

# Restaurar um arquivo específico
tar -xzf backups/backup_input_20240115_020001.tar.gz -C /destino/ input/arquivo_especifico.csv
```

**Configurar agendamento com cron:**
```bash
# Abrir editor do crontab
crontab -e

# Backup diário às 02:00
0 2 * * * /caminho/para/automation-suite/scripts/backup_automation.sh >> /caminho/para/automation-suite/logs/cron_backup.log 2>&1

# Backup semanal (domingo às 03:30) em modo dry-run para validação
30 3 * * 0 /caminho/para/automation-suite/scripts/backup_automation.sh --dry-run

# Verificar crontab ativo
crontab -l
```

---

### 5. Monitor de Saúde do Sistema

Monitor operacional com alertas configuráveis, dashboard visual e exportação JSON.

```bash
# Exibir dashboard no terminal e salvar JSON
python scripts/system_health_check.py

# Especificar diretório de output e processos críticos
python scripts/system_health_check.py \
  --output-dir output \
  --processes nginx postgres redis

# Apenas dashboard, sem salvar JSON
python scripts/system_health_check.py --no-save

# Output em formato JSON puro (útil para pipelines)
python scripts/system_health_check.py --json
```

**Output esperado (dashboard):**
```
============================================================
  MONITOR DE SAÚDE DO SISTEMA  |  ✓ OK
  2024-01-15T14:35:22.847631
============================================================
  Host     : servidor-prod  (Linux 5.15.0)
  Uptime   : 12h 43m
============================================================
  CPU       : [####----------------]  18.5%
  Cores     : 8 lógicos / 4 físicos
  RAM       : [########------------]  42.3%
               6.8GB / 16.0GB
  
  DISCO:
  /             : [##########----------]  51.2%
                  102.4GB / 200.0GB livres: 97.6GB
  /home         : [####----------------]  22.7%
                  45.4GB / 200.0GB livres: 154.6GB

  REDE:
  Enviado  : 1234.56 MB  |  Recebido: 5678.90 MB

  PROCESSOS CRÍTICOS:
  Todos os 2 processos críticos estão rodando.

  ALERTAS ATIVOS: 0
============================================================
```

**Limiares de alerta (configuráveis no código):**
- CPU > 90% → alerta
- RAM > 80% → alerta
- Disco > 85% → alerta
- Processo crítico ausente → alerta

**Exit code:** 0 se OK, 1 se houver alertas críticos (compatível com scripts de CI/CD e cron).

---

## Configuração Avançada do Backup

Edite as variáveis no início de `backup_automation.sh`:

```bash
SOURCE_DIRS=(          # Diretórios que serão copiados
    "$BASE_DIR/input"
    "$BASE_DIR/output"
    "/var/www/html"    # Adicione quantos quiser
)

BACKUP_DEST="$BASE_DIR/backups"   # Onde os backups são salvos
MAX_BACKUPS=7                      # Máximo por diretório-fonte (FIFO)
COMPRESSION="gz"                   # gz (rápido) | bz2 (melhor compressão) | xz (máxima compressão)
```

---

## Logs

Todos os scripts geram logs estruturados em `logs/`:

```
logs/
├── organize_files.log        # Histórico do organizador
├── report_generator.log      # Histórico do gerador de relatórios
├── bulk_data_formatter.log   # Histórico do formatador
├── backup_automation.log     # Histórico de backups
├── cron_backup.log           # Output do cron (se configurado)
└── system_health.log         # Histórico do monitor de saúde
```

Formato de log:
```
2024-01-15 14:32:01 | INFO     | Mensagem descritiva
2024-01-15 14:32:02 | WARNING  | Aviso não crítico
2024-01-15 14:32:03 | ERROR    | Erro tratado
2024-01-15 14:32:04 | CRITICAL | Erro que encerrou a execução
```

---

## Como Publicar no GitHub

```bash
# 1. Inicializar repositório local
git init
git add .
git commit -m "feat: initial commit — operational automation suite"

# 2. Criar repositório no GitHub via CLI
gh repo create automation-suite --public --description "Suite de automação Python/Bash para tarefas operacionais"

# 3. Enviar código
git branch -M main
git remote add origin https://github.com/seu-usuario/automation-suite.git
git push -u origin main
```

**Boas práticas para o repositório:**
- Adicione tópicos (topics) no GitHub: `python`, `automation`, `bash`, `pandas`, `devops`, `data-processing`
- Ative o GitHub Actions para lint automático (flake8/ruff)
- Adicione um `CONTRIBUTING.md` se pretende colaboração externa
- Crie releases versionadas para cada conjunto de melhorias

---

## Como Apresentar no Currículo

### Descrição do Projeto (para seção de projetos)

> **Suite de Automação de Tarefas Operacionais** | Python 3.12 · pandas · Bash · psutil  
> Pipeline de 5 módulos automatizando tarefas operacionais repetitivas: organização de arquivos com detecção de duplicatas por hash MD5, processamento e consolidação de grandes volumes de dados CSV com exportação para Excel formatado, padronização em massa via regex (nomes, telefones, emails, datas), backup comprimido e versionado com rotação automática via Bash/cron, e monitor de saúde de infraestrutura com alertas de limiar e geração de relatórios JSON históricos.

### Habilidades demonstradas por script

| Script | Habilidades demonstradas |
|---|---|
| `organize_files.py` | pathlib, hashlib, logging, tratamento de exceções, CLI (argparse) |
| `report_generator.py` | pandas (merge, limpeza, deduplicação), openpyxl, formatação Excel, métricas |
| `bulk_data_formatter.py` | regex, data wrangling, pipeline de transformação, validação de dados |
| `backup_automation.sh` | Bash scripting, tar, cron, tratamento de erros com set -euo pipefail |
| `system_health_check.py` | psutil, subprocess, JSON, monitoramento de sistema, exit codes |

### Como transformar em experiência profissional forte

1. **Quantifique o impacto**: "Reduziu em X horas/semana o tempo gasto em organização manual de arquivos"
2. **Contextualize o problema**: "Desenvolvido para automatizar rotinas operacionais de manipulação de dados em ambiente corporativo"
3. **Mencione a confiabilidade**: "Com logging estruturado, tratamento de exceções e dry-run para validação antes da execução"
4. **Destaque a observabilidade**: "Geração de relatórios históricos JSON e logs persistentes para auditoria"
5. **Relacione com vagas-alvo**:
   - **Backend Python**: pandas, pathlib, logging, argparse, arquitetura modular
   - **Automação/DevOps Jr**: Bash, cron, backup, monitoramento, subprocess
   - **Analista de Dados**: pandas, openpyxl, limpeza de dados, formatação Excel
   - **Python Developer**: código limpo, estrutura de projeto, boas práticas

---

## Licença

MIT — veja [LICENSE](LICENSE) para detalhes.
