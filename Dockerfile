# FastAPI-ready image for the future Bandhan backend service.
# No application code is included during repository initialization.
FROM python:3.12-slim

# Keep Python output predictable inside containers.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Prepare the application workspace.
WORKDIR /app

# Install only the web runtime required by the planned FastAPI service.
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir fastapi uvicorn

# Copy the intentionally empty backend module placeholder.
COPY backend/ /app/backend/

# The port reserved for the future FastAPI service.
EXPOSE 8000

# Application startup is defined when FastAPI source is introduced in a later phase.
CMD ["sh", "-c", "echo 'Bandhan backend placeholder: no application source is included in Review 1.' && tail -f /dev/null"]
