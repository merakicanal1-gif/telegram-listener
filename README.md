# Telegram Listener

Este é um serviço que escuta mensagens do Telegram em tempo real utilizando a biblioteca Telethon e encaminha os dados estruturados e mídias para um Webhook de sua escolha.

O projeto foi projetado para rodar de forma segura em ambientes de containerização como **Docker**, **Docker Compose** e **EasyPanel**, evitando logins interativos em produção e permitindo validações automáticas antes do deploy.

---

## Estrutura do Projeto

```
.
├── .dockerignore          # Evita cópia de arquivos locais/temporários na imagem Docker
├── .env.example           # Exemplo de variáveis de ambiente
├── .gitignore             # Ignora arquivos de sessão e logs no Git
├── Dockerfile             # Imagem Docker otimizada para produção (Slim, sem logs ou sessões embutidas)
├── docker-compose.yml     # Orquestração local do listener + servidor temporário de upload
├── create_session.py      # Script utilitário interativo para criar o arquivo de sessão localmente
├── main.py                # Único ponto de entrada da aplicação (suporta modo normal e --check)
├── requirements.txt       # Dependências da aplicação
├── app/                   # Módulos internos da aplicação
│   ├── client.py          # Gerenciamento de conexão e validação de autenticação da sessão
│   ├── config.py          # Validação e gerenciamento de variáveis de ambiente
│   ├── handlers.py        # Registro dos manipuladores de eventos do Telegram (ex: NewMessage)
│   ├── listener.py        # Orquestrador do listener do Telegram
│   ├── logger.py          # Logger estruturado (configurável para console ou arquivo)
│   ├── media.py           # Download e upload temporário de mídias
│   └── webhook.py         # Encaminhamento das mensagens estruturadas para o Webhook
└── sessions/
    └── .gitkeep           # Garante a existência do diretório de sessões
```

---

## Variáveis de Ambiente

Configure as seguintes variáveis de ambiente no seu arquivo `.env` (ou no painel do EasyPanel):

| Variável | Descrição | Valor Padrão | Obrigatória? |
| :--- | :--- | :--- | :--- |
| `API_ID` | ID da API do Telegram (obtenha em [my.telegram.org](https://my.telegram.org)) | - | **Sim** |
| `API_HASH` | Hash da API do Telegram (obtenha em [my.telegram.org](https://my.telegram.org)) | - | **Sim** |
| `SESSION_NAME` | Caminho do arquivo de sessão do Telethon (sem a extensão `.session`) | `sessions/telegram` | Não |
| `WEBHOOK_URL` | URL de destino do webhook (ex: n8n, Make, servidor próprio) | - | Não |
| `LOG_LEVEL` | Nível de detalhamento do log (`DEBUG`, `INFO`, `WARNING`, `ERROR`) | `INFO` | Não |
| `LOG_TO_FILE` | Gravar logs em arquivo na pasta `logs/` (defina como `false` no Docker) | `true` (local) / `false` (Docker) | Não |
| `UPLOAD_URL` | Endpoint para fazer upload temporário de mídias | `http://localhost:8000/upload` | Não |
| `MEDIA_UPLOAD_TIMEOUT` | Tempo máximo (em segundos) para aguardar o upload de mídias | `60` | Não |
| `DEFAULT_TTL` | Tempo de expiração (TTL em segundos) padrão para mídias do Telegram | `86400` (24h) | Não |

---

## Como Criar a Sessão (.session)

O Telethon exige uma autenticação inicial que requer um código enviado por SMS ou pelo próprio Telegram. Como os containers Docker rodando em produção (ou EasyPanel) não possuem terminal interativo, **você deve gerar a sessão localmente na sua máquina de desenvolvimento primeiro**.

1. Crie o arquivo `.env` na raiz do projeto e configure seu `API_ID` e `API_HASH`:
   ```bash
   API_ID=12345678
   API_HASH=sua_api_hash_aqui
   ```

2. Instale as dependências locais:
   ```bash
   pip install -r requirements.txt
   ```

3. Execute o script de login interativo:
   ```bash
   python create_session.py
   ```

4. Digite seu número de telefone e o código de verificação enviado pelo Telegram.
5. Se tudo der certo, o arquivo de sessão será criado em `sessions/telegram.session`.

---

## Como Rodar Localmente (Desenvolvimento)

Depois de criar a sessão com o passo anterior, você pode iniciar o listener localmente:

```bash
python main.py
```

Você verá logs parecidos com estes:
```text
2026-07-27 12:00:00,000 | INFO | ✔ Configuração carregada
2026-07-27 12:00:00,050 | INFO | ✔ Sessão encontrada
2026-07-27 12:00:00,051 | INFO | Conectando ao Telegram...
2026-07-27 12:00:01,200 | INFO | ✔ Conectado ao Telegram
2026-07-27 12:00:01,500 | INFO | ✔ Conectado como: Seu Nome (12345678)
2026-07-27 12:00:01,501 | INFO | ✔ Escutando mensagens...
```

---

## Como Rodar no Docker & Docker Compose

O Dockerfile foi construído para ser seguro em produção. Ele **não** embute arquivos de sessão na imagem e os logs em arquivo ficam desligados por padrão para preservar o disco do container. A sessão deve ser fornecida obrigatoriamente através de volumes montados no host.

### 1. Rodando com Docker Compose

O arquivo `docker-compose.yml` monta a pasta local `./sessions` no container.

1. Garanta que a sessão gerada (`telegram.session`) está na pasta `./sessions` do host.
2. Inicie os containers:
   ```bash
   docker compose up --build -d
   ```
3. Acompanhe os logs:
   ```bash
   docker compose logs -f
   ```

---

## Como Fazer Deploy no EasyPanel

O EasyPanel monta apenas volumes persistentes. Para o correto funcionamento do listener do Telegram, precisamos montar um volume para que a sessão persista entre restarts da aplicação.

### 1. Configurando o Volume no EasyPanel
No painel do seu serviço no EasyPanel:
1. Vá até as configurações de **Volumes**.
2. Adicione um novo volume montando a pasta de sessão do Host no Container:
   - **Host Path:** `/opt/telegram-listener/sessions` (ou qualquer diretório persistente no host VPS)
   - **Mount Path:** `/app/sessions`

### 2. Configurando as Variáveis de Ambiente no EasyPanel
Adicione em **Environment Variables (Env)**:
```env
API_ID=seu_api_id
API_HASH=seu_api_hash
SESSION_NAME=/app/sessions/telegram
LOG_TO_FILE=false
WEBHOOK_URL=https://seu-webhook.com/endpoint
UPLOAD_URL=http://seu-servidor-upload:8000/upload
```

### 3. Colocando o Arquivo de Sessão na VPS
Antes de iniciar o serviço na VPS, você deve fazer o upload do arquivo `telegram.session` criado localmente para a pasta correspondente no host da VPS:
```bash
scp sessions/telegram.session usuario@sua-vps:/opt/telegram-listener/sessions/telegram.session
```

### 4. Validação Pré-Deploy / Healthcheck (`--check`)
O ponto de entrada suporta o argumento `--check`. Esse comando valida as configurações e a sessão e encerra com código `0` se estiver tudo OK, ou `1` se houver falha, sem travar o terminal.

Você pode configurar a inicialização do container ou o healthcheck do EasyPanel usando o comando:
```bash
python main.py --check
```

Caso o EasyPanel tente iniciar o listener sem o arquivo de sessão montado corretamente, a aplicação não tentará iniciar uma autenticação interativa (o que geraria loops infinitos de reinício e `EOFError`). Em vez disso, ela exibirá um log de erro claro no console e finalizará o processo com código `1`:
```text
2026-07-27 12:00:00,000 | ERROR | ✘ Erro fatal: Arquivo de sessão não encontrado em /app/sessions/telegram.session
2026-07-27 12:00:00,001 | ERROR | ✘ Encerrando aplicação
```
