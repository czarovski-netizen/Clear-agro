# Revisao de Governanca - CRM Clear Agro

Data: 2026-02-22
Escopo: CRM apenas (app Streamlit, base_unificada.xlsx, metas.db, caches Bling/NFe)
Metodo: leitura de configuracoes, inventario de dados e verificacoes de consistencia basica.

## 1) Sumario executivo

Status geral: **Parcialmente adequado**, com riscos de acesso e governanca operacional.

Principais riscos (P0/P1):
- **P0 | Segregacao de acesso gestor vs diretor nao aplicada**: `data/access_control.json` nao define allow/block, entao o perfil gestor enxerga todos os vendedores/dados. Isso expõe dados B2B/familia e metas completas.
- **P1 | Dados sensiveis misturados na mesma base operacional**: `base_unificada.xlsx` e caches Bling contem dados completos; sem camada de anonimização/particao para o app do gestor.
- **P1 | Linhagem entre metas.db e base_unificada sem reconciliacao formal**: metas mensais existem em ambos, mas nao ha rotina de reconciliacao documentada (apenas validacao manual).

Pontos positivos:
- Estrutura de dados organizada e padroes descritos em `docs/OPERATING_MANUAL.md` e `docs/DATA_DICTIONARY.md`.
- Camadas e fluxos definidos para Control Tower (apesar de fora do escopo do CRM).
- Caches Bling/NFe estruturados e nomeados por ano.

## 2) Inventario de dados e superficies

Fontes ativas:
- `out/base_unificada.xlsx`
  - Abas: oportunidades, atividades, realizado, clientes_dim, metas
  - Realizado: 60 linhas; anos 2025-2026
  - Metas: 180 linhas (metas mensais)
  - Oportunidades: 86 linhas
- `data/metas.db`
  - 180 linhas (mes a mes)
  - Ano 2026, 15 vendedores, 7 UFs
  - Meta total: R$ 12.200.000
- `bling_api/*.jsonl`
  - vendas_2025/2026, nfe_2025/2026, contas a pagar/receber, produtos, contatos, estoque

Superficies de acesso:
- `app/main.py` (diretor e regras base)
- `app/gestor.py` (perfil gestor)
- `app/diretor.py` (perfil diretor)
- `data/access_control.json` (ACL atual)

## 3) Avaliacao por dominio

### Acesso & Privacidade
- ACL existe, mas **nao aplicada** (allow/block vazio). Isso permite acesso total no app de gestor.
- Nao ha mascara/anonimizacao de clientes B2B.

Risco: P0

### Qualidade & Linhagem
- Dicionario de dados e manual existem.
- Base unificada e metas.db convivem sem reconciliacao formal.
- Falta registro automatico de variacoes entre base_unificada e metas.db.

Risco: P1

### Controles Operacionais
- Runbook definido (docs), mas nao ha evidencia de:
  - versionamento de input por periodo
  - log de atualizacao do CRM (timestamp de refresh)

Risco: P1

## 4) Recomendações priorizadas

### P0 (imediato)
1. **Aplicar segregacao de acesso** no `data/access_control.json`:
   - Definir allow-list para gestores (somente vendedores permitidos)
   - Validar no app gestor (filtro efetivo de metas, realizado, oportunidades)
2. **Separar deploys** (diretor e gestor), com bases distintas se necessario.

### P1 (curto prazo)
3. **Criar reconciliacao automatica** entre metas.db e base_unificada (metas por mes/vendedor)
4. **Definir politica de dados sensiveis** (clientes B2B, familias) e camadas segregadas

### P2 (medio prazo)
5. **Implementar log de refresh** do CRM e checklist de publicacao
6. **Validacoes adicionais** (ex.: metas negativas, datas faltantes, vendedor inexistente)

## 5) Backlog sugerido (resumo)

- [P0] Definir allow-list para gestor (por vendedor e/ou empresa)
- [P0] Criar dataset filtrado para gestor (sem B2B e familia)
- [P1] Relatorio de reconciliacao metas.db x base_unificada
- [P1] Log de atualizacao do CRM (data/hora e responsavel)
- [P2] Painel de qualidade com alertas de dados faltantes

## 6) Evidencias (arquivos)
- `data/access_control.json`
- `app/main.py`, `app/gestor.py`, `app/diretor.py`
- `out/base_unificada.xlsx`
- `data/metas.db`
- `bling_api/nfe_2026_cache.jsonl`, `bling_api/vendas_2026_cache.jsonl`
