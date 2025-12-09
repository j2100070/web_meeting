FROM python:3.9

WORKDIR /code

COPY requirements.txt .
# コンテナ内でpipをアップグレード
RUN pip install --upgrade pip

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["celery", "-A", "mtgsys", "worker", "-l", "info"]
