FROM mcr.microsoft.com/playwright/python:v1.59.0-jammy

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["xvfb-run", "--auto-servernum", "--server-args=-screen 0 1280x720x24", "python", "scirate_discord_bot.py"]
