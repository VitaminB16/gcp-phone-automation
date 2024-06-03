FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y gconf-service libasound2 libatk1.0-0 libcairo2 libcups2 libfontconfig1 libgdk-pixbuf2.0-0 libgtk-3-0 libnspr4 libpango-1.0-0 libxss1 fonts-liberation libappindicator1 libnss3 lsb-release xdg-utils wget \
    && wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && dpkg -i google-chrome-stable_current_amd64.deb; apt-get -fy install


# Allows docker to cache installed dependencies between builds
WORKDIR /tmp

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Sets the working directory back to the root of the container
WORKDIR /app

# Copies the local code to the container
COPY . .

CMD ["python", "main.py"]
