FROM python:3

COPY ./requirements.txt /app/requirements.txt
COPY ./app.py /app/app.py


WORKDIR /app

RUN pip install -r requirements.txt

COPY . /app

EXPOSE 8080
ENV NAME Dashboard

ENTRYPOINT [ "python" ]

CMD [ "app.py" ]
