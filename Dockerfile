FROM python:3.13
RUN pip install pipenv
WORKDIR /app
COPY Pipfile Pipfile.lock /app/
RUN pipenv install --deploy --system
COPY . /app
CMD ["python", "assistant.py"]
