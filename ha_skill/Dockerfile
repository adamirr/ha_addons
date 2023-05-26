ARG BUILD_FROM
FROM ${BUILD_FROM}

# Install requirements for add-on
RUN apk add --no-cache python3 py3-pip
RUN pip3 install --upgrade pip
RUN pip3 install --no-cache-dir requests boto3

# Copy data for add-on
COPY run.py /
COPY cloudformation.yaml /

ENTRYPOINT [ "python3" ]
CMD [ "/run.py" ]