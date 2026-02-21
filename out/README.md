# McKinsey Agro CRM

## Como rodar
- `streamlit run app/main.py`

## Fonte de dados
- `out/base_unificada.xlsx`
- Abas esperadas: `oportunidades`, `realizado`, `metas`, `atividades`.

## Realizado do Bling (opcional)
- Cache: `bling_api/vendas_2026_cache.jsonl` (fallback 2025)
- Mapeamento de vendedor: `bling_api/vendedores_map.csv` com colunas `vendedor_id,vendedor`

## Atualizar dados
- Substitua o arquivo `out/base_unificada.xlsx` mantendo as abas e colunas.
- Rode `python scripts/validate_kpis.py` para validar.

## Estrutura
- `src/data.py` leitura
- `src/metrics.py` calculos
- `src/viz.py` graficos/formatacao
- `app/main.py` UI
