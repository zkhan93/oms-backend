FROM python:3.8-slim

COPY install-packages.sh .
RUN ./install-packages.sh

RUN pip install --upgrade pip

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .

EXPOSE 80

ENTRYPOINT  ["bash","run.sh"]
CMD ["gunicorn", "oms.wsgi", "-b", "0.0.0.0:80", "--access-logfile", "-"]
