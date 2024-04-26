FROM public.ecr.aws/lambda/python:latest

WORKDIR ${LAMBDA_TASK_ROOT}

RUN --mount=type=bind,source=requirements.txt,target=requirements.txt \
    pip install -r requirements.txt

COPY extract_flood.py .
COPY transform_flood.py .
COPY load_flood.py .
COPY pipeline_flood.py .

CMD ["pipeline_flood.handler"]
