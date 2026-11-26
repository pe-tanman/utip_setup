# Build from the repo root:  docker build -f discord/bot/Dockerfile -t utip-bot .
FROM python:3.12-slim
WORKDIR /app
COPY pipeline/utip /app/pipeline/utip
COPY discord/bot /app/discord/bot
RUN pip install --no-cache-dir -r /app/discord/bot/requirements.txt
CMD ["python", "/app/discord/bot/bot.py"]
