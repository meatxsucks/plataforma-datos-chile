FROM python:3.12-slim
RUN pip install --no-cache-dir boto3 docker
WORKDIR /app
COPY app.py .
CMD ["python", "-u", "app.py"]
