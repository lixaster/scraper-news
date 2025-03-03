FROM lixaster/scraper-news:base

WORKDIR /app
COPY ./*.py ./
COPY ./config/config.yaml ./config/config.yaml

CMD ["python", "main.py"]
