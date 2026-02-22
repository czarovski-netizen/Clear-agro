# Checklist de Governanca - CRM Clear Agro

Data: 2026-02-22

## Acesso & Privacidade
- [ ] ACL definida para perfil gestor (allow-list por vendedor/empresa)
- [ ] Perfil gestor nao visualiza clientes B2B/familia
- [ ] Segredos e tokens (Bling/Telegram) fora do repo e configurados via secrets
- [ ] Dados sensiveis anonimizados/segregados em dataset especifico

## Qualidade & Linhagem
- [ ] Base unificada com datas validas (sem nulos)
- [ ] Metas.db reconciliadas com base_unificada (metas mensais)
- [ ] Dicionario de dados atualizado (campos novos)
- [ ] Logs de qualidade gerados e revisados periodicamente

## Controles Operacionais
- [ ] Runbook de atualizacao mensal seguido
- [ ] Log de refresh do CRM (data/hora, responsavel, input)
- [ ] Backups dos inputs antes de processamento
- [ ] Reprocessamento deterministico documentado

## Seguranca Operacional
- [ ] Separacao de deploys diretor x gestor
- [ ] Acesso ao app gestor limitado a usuarios autorizados
- [ ] Revisao trimestral das permissoes

## Observacoes
- Estado atual: ACL vazia permite acesso total no perfil gestor.
- Metas completas em `metas.db` e `base_unificada.xlsx` sem reconciliacao automatica.
