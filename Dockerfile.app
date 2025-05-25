FROM lixaster/scraper-news:base

WORKDIR /app
COPY ./*.py ./
COPY ./config/config-example.yaml ./config/config.yaml
COPY ./config/secret-example.yaml ./config/secret.yaml

CMD ["python", "main.py"]
