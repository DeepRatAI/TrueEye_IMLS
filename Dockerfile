FROM python:3.10-slim

# Install dependencies
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Copy flow file and assets
WORKDIR /app
COPY trueeye_flow.json ./
COPY .assets ./assets

# Expose the port used by LangFlow
EXPOSE 7860

# Run the LangFlow server
CMD ["langflow", "run", "trueeye_flow.json", "--host", "0.0.0.0", "--port", "7860"]
