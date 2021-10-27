FROM python:3.9-buster

COPY . /app

WORKDIR /app

RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN pip install -e .

CMD ["uvicorn", "API.main:app", "--reload", "--host", "0.0.0.0"]