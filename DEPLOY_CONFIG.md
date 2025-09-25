# Configuração para Deploy - 4M Pagamentos

## Problema Identificado

Quando você faz deploy no Git, o sistema pode estar tentando usar o **4M Pagamentos** mas sem as chaves de API configuradas, causando erro.

## Solução Implementada

✅ **Fallback Automático**: Se `GATEWAY_CHOICE=4M` mas `QUATROM_PAGAMENTOS_SECRET_KEY` não estiver configurada, o sistema automaticamente usa **For4Payments** como backup.

## Configuração Necessária no Deploy

Para usar o **4M Pagamentos** em produção, configure estas variáveis de ambiente:

```bash
GATEWAY_CHOICE=4M
QUATROM_PAGAMENTOS_SECRET_KEY=3mpag_kdnf2w9jq_mfagk31e
```

## Alternativas

### Opção 1: Usar For4Payments (Padrão)
```bash
GATEWAY_CHOICE=FOR4
FOR4PAYMENTS_SECRET_KEY=sua_chave_for4
```

### Opção 2: Usar NovaEra Payments  
```bash
GATEWAY_CHOICE=NOVAERA
NOVAERA_SECRET_KEY=sua_chave_novaera
```

### Opção 3: Usar 4M Pagamentos
```bash
GATEWAY_CHOICE=4M
QUATROM_PAGAMENTOS_SECRET_KEY=3mpag_kdnf2w9jq_mfagk31e
```

## Como Configurar no Seu Ambiente de Deploy

Dependendo da plataforma:

- **Heroku**: `heroku config:set GATEWAY_CHOICE=4M`
- **Vercel**: Adicionar nas Environment Variables
- **Railway**: Configurar nas Variables  
- **Outros**: Adicionar no painel de configuração

O sistema agora é **tolerante a falhas** e não quebra se as chaves não estiverem configuradas.