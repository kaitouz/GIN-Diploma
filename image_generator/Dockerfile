FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

# CMD ["python", "generator.py"]
# CMD ["python", "worker.py"]

# CMD ["rq", "worker", "-u", " redis://redis:6379",  "generate_tasks"]
CMD rq worker -u redis://redis:6379 generate_tasks
# CMD ["ls ../"]