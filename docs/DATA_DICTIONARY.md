# Data Dictionary

## Camadas
- raw: dados de origem imutaveis
- staging: padronizacao de colunas/tipos
- marts: tabelas analiticas finais
- exports: saidas para diretoria
- quality: logs de validacao

## Tabelas esperadas
- data/staging/stg_dre.csv
- data/staging/stg_bling.csv
- data/staging/stg_banks.csv
- data/marts/fact_dre.csv
- data/marts/fact_cashflow.csv
- data/marts/fact_reconciliation.csv
- data/marts/fact_forecast.csv

## Campos minimos por transacao
- source
- raw_id
- hash
- data
- valor
- descricao
- entidade
- account_code
- cost_center_id
- country
