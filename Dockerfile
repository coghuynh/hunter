FROM python:3.11-slim

WORKDIR /app
COPY . /app

RUN pip install -r requirements.txt

ENV ENV=.env.hunter

EXPOSE 8000

CMD ["python3", "src/app.py"]

