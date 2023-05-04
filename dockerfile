FROM python:3.9-slim-buster

WORKDIR /app

COPY appv3.py examples/ /app/

COPY templates/ /app/templates

COPY static/ /app/static/

COPY requirements.txt /app/

RUN pip install -r requirements.txt 

CMD ["python", "appv3.py"]