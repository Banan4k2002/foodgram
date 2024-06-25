FROM python:3.9

WORKDIR /app

RUN pip install gunicorn==20.1.0

COPY /data .

COPY requirements.txt .

RUN pip install -r requirements.txt --no-cache-dir

COPY . .

ENTRYPOINT ["sh", "entrypoint.sh"]