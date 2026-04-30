FROM mcr.microsoft.com/playwright/python:v1.59.0-jammy

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["sh", "-c", "echo '>>> container started, launching xvfb-run...'; exec xvfb-run --auto-servernum --server-args='-screen 0 1280x720x24' python -u scirate_discord_bot.py 2>&1"]
