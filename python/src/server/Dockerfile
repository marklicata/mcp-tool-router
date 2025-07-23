FROM python:3.11-slim

# Set working directory inside container
WORKDIR /

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy only the server part
COPY . .

# Expose the expected port
EXPOSE 8000

# Launch FastAPI app (update if your server file uses a different entry point)
CMD ["uvicorn", "run:app", "--host", "0.0.0.0", "--port", "8000"]