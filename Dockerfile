
FROM python:3.11-alpine


ENV My_APP /app

WORKDIR &My_APP

COPY . .

EXPOSE 3000

VOLUME $My_APP/storage

ENTRYPOINT ["python", "main.py"]