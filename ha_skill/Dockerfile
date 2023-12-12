ARG BUILD_FROM
FROM ${BUILD_FROM}

# Install requirements for add-on
RUN apk add --no-cache python3 py3-pip py3-requests py3-boto3

# Copy data for add-on
COPY run.py /
COPY cloudformation.yaml /

ENTRYPOINT [ "python3" ]
CMD [ "/run.py" ]
