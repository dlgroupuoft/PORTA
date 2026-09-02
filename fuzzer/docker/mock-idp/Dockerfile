FROM python:3.12-slim

RUN pip install --no-cache-dir PyJWT[crypto] cryptography signxml lxml

WORKDIR /app
COPY server.py .

EXPOSE 9090
CMD ["python3", "server.py"]
