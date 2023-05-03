FROM python:3.9-slim-buster

WORKDIR /app

COPY appv1.py examples/ /app/

COPY requirements.txt /app/

RUN pip install -r requirements.txt 

CMD ["python", "appv1.py"]