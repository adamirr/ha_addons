FROM alpine:3.20.2

# Install requirements for add-on
RUN apk add --no-cache python3 py3-pip py3-requests py3-boto3

# Copy data for add-on
COPY run.py /
COPY cloudformation.yaml /

RUN mkdir /data
RUN touch /data/options.json

ENTRYPOINT [ "python3" ]
CMD [ "/run.py" ]
