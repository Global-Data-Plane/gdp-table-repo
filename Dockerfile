FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src
COPY static ./static
COPY templates ./templates

ENV PYTHONPATH="/app"
ENV FLASK_APP=src/app.py
ENV FLASK_ENV=development
ENV FLASK_STATIC_ASSET_DIR=/app/static
ENV FLASK_JINJA_TEMPLATE_DIR=/app/templates

EXPOSE 5000

CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]
