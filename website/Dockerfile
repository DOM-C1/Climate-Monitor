 
FROM python:latest

copy . static
COPY . app.py
COPY . templates
COPY . utils.py
COPY . utils_db.py
COPY .requirements.txt

RUN pip install -r requirements.txt

EXPOSE 80

CMD ["python", "app.py"]
