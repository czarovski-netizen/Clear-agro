# Auditoria do App

## Arquivo principal

- C:\Users\cesar.zarovski\app\main.py

## Fontes de dados

- C:\Users\cesar.zarovski\out\base_unificada.xlsx

## Schema real (colunas)

- oportunidades: ['id_oportunidade', 'cliente', 'canal', 'volume_potencial', 'vendedor', 'etapa']
- atividades: []
- realizado: ['data', 'cliente', 'produto', 'receita', 'vendedor', 'origem']
- testes: []
- clientes_dim: []
- metas: ['data', 'vendedor', 'meta', 'realizado']

## KPIs e formulas atuais

- Realizado YTD: soma de receita em realizado para o ano (coluna data)
- Meta YTD: soma de meta em metas para o ano ate o mes atual
- Atingimento %: realizado_ytd / meta_ytd (se meta=0 => 0)
- Pipeline Total: soma de volume_potencial em oportunidades
- Pipeline Ponderado: volume_potencial * probabilidade (se existir)
- % com proximo passo: proporcao de data_proximo_passo nao nula

## Possiveis causas de bugs

- Colunas ausentes: data_proximo_passo, probabilidade, volume_potencial
- Tipos errados em meta/realizado (texto em vez de numero)
- Metas sem data ou data fora do ano => meta_ytd = 0
- Oportunidades sem valor => pipeline_total = 0
- Realizado sem data => YTD nao filtra corretamente