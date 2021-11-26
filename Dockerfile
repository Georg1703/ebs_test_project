FROM python:3
ENV PYTHONUNBUFFERED=1
COPY ./project project
WORKDIR /project
RUN pip install -r requirements.txt
