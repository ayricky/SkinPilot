FROM python:3.11

# Set the working directory
WORKDIR /app

# Install system-level dependencies
# RUN apt-get update && \
#     apt-get install -y libsndfile1 libportaudio2 portaudio19-dev ffmpeg && \
#     apt-get clean && \
#     rm -rf /var/lib/apt/lists/*

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
