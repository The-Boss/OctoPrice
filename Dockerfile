FROM python:3.11-slim

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./app /code/app

#EXPOSE 8000

CMD ["fastapi", "run", "app/main.py", "--port", "80"]

#CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]


# If running behind a proxy like Nginx or Traefik add --proxy-headers
# CMD ["fastapi", "run", "app/main.py", "--port", "80", "--proxy-headers"]