FROM python:3.12-slim

WORKDIR /app

# Instala dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia código necessário
COPY app/ ./app/
COPY main.py .

# Cria a pasta de sessões
RUN mkdir -p sessions

# Variáveis de ambiente padrão para produção
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    SESSION_NAME=/app/sessions/telegram \
    LOG_TO_FILE=false

CMD ["python", "main.py"]
