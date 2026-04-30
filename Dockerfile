FROM mcr.microsoft.com/playwright/python:v1.59.0-jammy

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["sh", "-c", "echo '>>> [1/4] container started'; Xvfb :99 -screen 0 1280x720x24 -nolisten tcp & echo '>>> [2/4] Xvfb started PID='$!; sleep 2; export DISPLAY=:99; echo '>>> [3/4] DISPLAY='$DISPLAY' running python'; exec python -u scirate_discord_bot.py 2>&1"]
