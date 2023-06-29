FROM python:3.11

# Set the working directory
WORKDIR /app

# Install Poetry
RUN pip install poetry

# Copy the pyproject.toml and poetry.lock files to the container
COPY pyproject.toml poetry.lock ./

# Install dependencies using Poetry
RUN poetry config virtualenvs.create false && poetry install --only main

# Copy the rest of the application files
COPY . .

# Set the entrypoint for your application (adjust this according to your needs)
CMD ["python", "src/bot.py"]
