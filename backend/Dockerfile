FROM python:3.13-slim

# Keep runtime containers free from bytecode files and buffered logs.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copy dependency metadata before source to preserve the install cache layer.
COPY pyproject.toml README.md ./
COPY app ./app

# Install only runtime dependencies declared by the package.
RUN pip install --no-cache-dir .

EXPOSE 8000

# Bind all interfaces so the process is reachable through the container network.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
