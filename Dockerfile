FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src
COPY static ./static
COPY templates ./templates

EXPOSE 5000

CMD ["gunicorn", "-w", "1", "-b", "0.0.0.0:5000", "src.app:create_app()"]
