# Use the official AWS Lambda Python base image
FROM public.ecr.aws/lambda/python:3.12

# Copy requirements first (for caching)
COPY requirements.txt ${LAMBDA_TASK_ROOT}
RUN pip install -r requirements.txt

# Copy your bot code
COPY bot.py ${LAMBDA_TASK_ROOT}

# Set the handler (file_name.function_name)
CMD [ "bot.lambda_handler" ]