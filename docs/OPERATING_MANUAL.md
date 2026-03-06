# Operating Manual - Control Tower Financeira

## Objetivo
Operar mensalmente o fluxo financeiro end-to-end com rastreabilidade completa.

## Premissas
- Nunca alterar arquivos em `data/raw`.
- Ajustes manuais somente em `config/overrides/*.csv`.
- Reprocessamento sempre deve gerar os mesmos resultados com os mesmos inputs.

## Calendario mensal sugerido
- D+1 a D+3: coleta de DRE parcial, Bling e extratos.
- D+4: ingestao e padronizacao.
- D+5: classificacao e overrides.
- D+6: reconciliacao competencia vs caixa.
- D+7: CFO Pack e revisao executiva.

## Passo a passo operacional
1. Depositar arquivos novos em:
   - `data/raw/dre`
   - `data/raw/bling`
   - `data/raw/banks`
2. Executar ingestao:
   - `python src/ingest/ingest_dre.py`
   - `python src/ingest/ingest_bling.py`
   - `python src/ingest/ingest_banks.py`
3. Revisar logs de qualidade em `data/quality/*.json`.
4. Preencher overrides em `config/overrides/overrides_template.csv` e versionar.
5. Gerar mart e pacote executivo:
   - `python src/reports/build_cfo_pack.py`
6. Validar outputs:
   - `data/marts/fact_reconciliation.csv`
   - `data/exports/cfo_pack.md`
   - `data/exports/cfo_pack_executive_summary.csv`
7. Compartilhar CFO Pack com diretoria.

## Checklist de controle
- [ ] Sem duplicidade por hash nas tabelas staging.
- [ ] Datas validas e moeda coerente.
- [ ] Divergencias materiais listadas em reconciliation exceptions.
- [ ] Overrides revisados e aprovados.
- [ ] CFO Pack publicado.

## Troubleshooting
- Staging vazio: verificar se ha arquivos em `data/raw/*`.
- Campos nao mapeados: revisar sugestoes em `data/quality/*_ingest_report.json`.
- Divergencia alta competencia vs caixa: validar AR/AP, timing e impostos.

## Governanca
- Responsavel tecnico: time de dados/finance.
- Responsavel de negocio: CFO Office.
- Auditoria: manter historico de overrides e logs de qualidade por periodo.
