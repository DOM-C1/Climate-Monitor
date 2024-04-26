FROM public.ecr.aws/lambda/python:latest
WORKDIR ${LAMBDA_TASK_ROOT}
RUN --mount=type=bind,source=requirements.txt,target=requirements.txt \
    pip install -r requirements.txt
COPY extract.py .
COPY transform.py .
COPY load.py .
COPY pipeline.py .
CMD ["pipeline.handler"]
