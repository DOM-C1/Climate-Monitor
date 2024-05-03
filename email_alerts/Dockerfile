FROM public.ecr.aws/lambda/python:latest
WORKDIR ${LAMBDA_TASK_ROOT}
RUN --mount=type=bind,source=requirements.txt,target=requirements.txt \
    pip install -r requirements.txt
COPY email_alert_setup.py . 
COPY create_email_messages.py .
COPY send_email.py .
COPY update_alerts.py .
CMD ["send_email.handler"]