FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directory for SQLite database
RUN mkdir -p /app/data

# Expose API port
EXPOSE 8000

# Create entrypoint script
RUN echo '#!/bin/bash\n\
python -m backend.main &\n\
BACKEND_PID=$!\n\
python -m bot.main &\n\
BOT_PID=$!\n\
wait $BACKEND_PID $BOT_PID' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

CMD ["/app/entrypoint.sh"]
