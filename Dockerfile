# Use a slim Python base image
FROM python:3.12-slim-bookworm

# Set the working directory in the container
WORKDIR /app

# Install system dependencies (espeak-ng is required by misaki)
# --no-install-recommends reduces image size by not installing recommended packages
# rm -rf /var/lib/apt/lists/* cleans up apt cache to keep image small
RUN apt-get update && apt-get install -y --no-install-recommends espeak-ng tzdata \
    && rm -rf /var/lib/apt/lists/*

# Set timezone (optional, default Asia/Taipei)
ENV TZ=Asia/Taipei

# Copy pyproject.toml and uv.lock (if you generate one) to leverage uv's caching
# This step is done early to allow Docker to cache the dependency installation layer
COPY pyproject.toml ./
# 若有 uv.lock 請取消下一行註解，否則保持註解避免 build 出錯
# COPY uv.lock ./

# Install uv itself
RUN pip install uv

# Install Python dependencies using uv from pyproject.toml
# `--system` installs into the Python environment (not a virtual environment, which is suitable for Docker)
# `.` refers to the current directory where pyproject.toml is located
RUN uv pip install --system .

# 安裝 spaCy 英文模型，避免 runtime 才下載
RUN python -m spacy download en_core_web_sm

# Copy the rest of the application code into the container
COPY . .

# Create a non-root user and switch to it
RUN useradd -m appuser && chown -R appuser /app
USER appuser

# Expose the port that Uvicorn will run on
EXPOSE 8000

# Command to run the application using Uvicorn
# The --host 0.0.0.0 makes the server accessible from outside the container
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
