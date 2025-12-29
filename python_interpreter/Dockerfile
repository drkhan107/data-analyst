
# # Use an official Python runtime as a parent image
# FROM python:3.11-slim

# # Set environment variables
# # PYTHONDONTWRITEBYTECODE: Prevents Python from writing pyc files to disc
# # PYTHONUNBUFFERED: Prevents Python from buffering stdout and stderr
# ENV PYTHONDONTWRITEBYTECODE=1
# ENV PYTHONUNBUFFERED=1

# # Set the working directory in the container
# WORKDIR /app

# # Install system dependencies
# # (gcc may be required for some pdfplumber/numpy dependencies)
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     build-essential \
#     && rm -rf /var/lib/apt/lists/*

# # Install python dependencies
# # COPY requirements.txt .

# RUN pip install --no-cache-dir \
#     pandas \
#     numpy \
#     matplotlib \
#     seaborn \
#     openpyxl \
#     pydantic \
#     langchain_experimental


# # Copy the source code
# COPY main.py .

# # Create the data directory (optional, but good practice)
# RUN mkdir -p /app/data

# # Define the command to run the script
# CMD ["python", "main.py"]




# Use a slim image for faster pull/start times
FROM python:3.12-slim

# Security: Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install only essential system libs
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*


# Pre-install dependencies to bake them into the image layers (Speed)
# COPY requirements.txt .
# RUN pip install -r requirements.txt
RUN pip install --no-cache-dir \
    pandas \
    numpy \
    matplotlib \
    seaborn \
    openpyxl \
    pydantic \
    tabulate 
    # langchain_experimental

## Create restricted user
RUN groupadd -r sandboxuser && useradd -r -g sandboxuser sandboxuser

# Setup data dir and fix perms
RUN mkdir -p /app/data && chown -R sandboxuser:sandboxuser /app /tmp /home

COPY main.py code_execution.py ./

# Security: Switch to non-privileged user
USER sandboxuser

CMD ["python", "main.py"]