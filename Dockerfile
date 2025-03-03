FROM python:3.12-slim-bookworm
ENV TZ=Asia/Shanghai

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt && \
    playwright install firefox && \
    playwright install-deps firefox && \
    apt-get update && \
    apt-get install -y --no-install-recommends vim && \
    apt-get clean

CMD ["python", "main.py"]