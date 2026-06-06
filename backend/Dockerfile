# Backend Lambda – local dev + testing image
FROM public.ecr.aws/lambda/python:3.12

WORKDIR ${LAMBDA_TASK_ROOT}

# Install shared dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all lambda source code
COPY lambdas/ ./lambdas/
COPY shared/   ./shared/

# Default to auth handler (override with --env HANDLER=patients.handler)
ENV HANDLER=auth.handler
CMD ["auth.handler.lambda_handler"]
