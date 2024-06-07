FROM python:3

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY run-game-simulation.py ./
COPY client.properties ./
COPY assets /assets

CMD [ "python", "./run-game-simulation.py" ]