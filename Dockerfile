FROM python:3.12.9

WORKDIR /usr/src/app

COPY requirements.txt /usr/src/app/

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "fastapi", "run", "apps/main.py", "--host", "0.0.0.0", "--port", "8000" ]