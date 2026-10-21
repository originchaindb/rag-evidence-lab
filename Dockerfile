FROM python:3.12-slim
WORKDIR /app
COPY app.py cloud.py logic.py ./
COPY examples ./examples
USER 65532:65532
ENTRYPOINT ["python","app.py"]
CMD ["run","examples/input.json"]
