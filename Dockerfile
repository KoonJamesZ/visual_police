FROM python:3.11.2

WORKDIR /workspace

COPY requirements.txt .

RUN pip3 install -r requirements.txt

COPY . .

EXPOSE 7860

ENTRYPOINT [ "python3", "app.py" ]