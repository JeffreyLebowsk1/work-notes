# Work Notes — GUI Docker image
# Builds and serves the Flask web GUI (tools/app.py) on port 5000.
#
# Build:  docker build -t work-notes-gui .
# Run:    docker run -p 5000:5000 work-notes-gui
#
# For live note editing, use docker-compose instead (mounts the repo as a volume).

FROM python:3.11-slim

# Prevent .pyc files and enable unbuffered stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_DEBUG=0

WORKDIR /workspace

# Install Python dependencies first (cached layer)
COPY tools/requirements-web.txt ./tools/requirements-web.txt
RUN pip install --no-cache-dir -r tools/requirements-web.txt

# Copy the rest of the repository
COPY . .

EXPOSE 5000

# Run the web GUI; app.py binds to 0.0.0.0:5000 in its __main__ block
CMD ["python3", "tools/app.py"]
