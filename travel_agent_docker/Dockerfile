# Start from a slim Python image
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your application code (including your agent.py)
COPY . .

# Set environment variables (e.g., for credentials or configuration)
ARG GOOGLE_API_KEY
ENV GOOGLE_GENAI_USE_VERTEXAI=0
ENV GOOGLE_API_KEY=$GOOGLE_API_KEY

# Expose the port (ADK API server defaults to 8000)
EXPOSE 8000

# Run the ADK API server when the container starts
# The AGENTS_DIR is the directory containing your agent definition
CMD ["adk", "api_server", "YOUR_AGENT_DIRECTORY_NAME", "--host", "0.0.0.0", "--port", "8000"]