import boto3
import botocore
import hashlib
import json
import logging
import os
import requests
import sys
import time
import urllib3
import uuid

logging.basicConfig(
    format='%(asctime)s %(levelname)-6s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S'
)
log = logging.getLogger('ha-skill')

# Max size is 256KiB (some buffer for MessageAttributes)
# https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/quotas-messages.html
MAX_MESSAGE_SIZE = 256000

# TODO: read from CloudFormation outputs
QUEUE_NAME = 'ha-skill-requests.fifo'

def handle_cloudformation_stack(session, stack_name, stack_params={}):
    log.info('Starting up!')
    cfn = session.client('cloudformation')
    with open('/cloudformation.yaml') as f:
        template_body = f.read()

    try:
        cfn.describe_stacks(StackName=stack_name)
        stack_exists = True
    except botocore.exceptions.ClientError as e:
        log.debug(f'decribe stack exception: {e}')
        stack_exists = False

    cfn_stack_parameters = [{'ParameterKey': k, 'ParameterValue': v} for k,v in stack_params.items()]
    if (not stack_exists):
        log.info(f'Creating CloudFormation stack {stack_name}')
        create_stack = cfn.create_stack(
            StackName=stack_name,
            TemplateBody=template_body,
            Parameters=cfn_stack_parameters,
            Capabilities=['CAPABILITY_IAM']
        )
        create_waiter = cfn.get_waiter('stack_create_complete')
        log.info(f'Waiting for stack {stack_name} to be created')
        create_waiter.wait(StackName=stack_name)
    else:
        log.info(f'CloudFormation stack {stack_name} already exists. Attempting an update')
        try:
            update_stack_response = cfn.update_stack(
                StackName=stack_name,
                TemplateBody=template_body,
                Parameters=cfn_stack_parameters,
                Capabilities=['CAPABILITY_IAM']
            )
            update_stack_waiter = cfn.get_waiter('stack_update_complete')
            update_stack_waiter.wait(StackName=stack_name)
            log.info(f'Stack {stack_name} was updated')
        except botocore.exceptions.ClientError as e:
            if str(e).endswith('No updates are to be performed.'):
                log.info(f'Stack {stack_name} is already up to date')
            else:
                raise e
    describe_stacks_response = cfn.describe_stacks(StackName=stack_name)
    assert len(describe_stacks_response['Stacks']) == 1
    stack_details = describe_stacks_response['Stacks'][0]
    outputs = {o['OutputKey']: o['OutputValue'] for o in stack_details['Outputs']}
    log.info(f'Stack has outputs\n{json.dumps(outputs, indent=2)}')


def poll_for_work(session,options):
    sqs = session.resource('sqs')
    request_queue = sqs.get_queue_by_name(QueueName=QUEUE_NAME)

    http = urllib3.PoolManager(
        timeout=urllib3.Timeout(connect=2.0, read=5.0)
    )

    token = os.environ.get('SUPERVISOR_TOKEN')
    if 'HA Token' in options:
        token=options['HA Token']
    assert token is not None

    request_url = 'http://supervisor/core/api/alexa/smart_home'
    if 'HA Base URL' in options:
        request_url=os.path.join(options['HA Base URL'],'api/alexa/smart_home')
    log.debug(f'request_url: "{request_url}"')    
        
    log.info(f'Polling for work from {QUEUE_NAME}...')
    while True:
        try:
            messages = request_queue.receive_messages(MaxNumberOfMessages=1, AttributeNames=['MessageGroupId'])
        except Exception as e:
            log.warning(f'Error polling for messages. Waiting 1 minute to try again. {e}')
            log.debug('Error:', exc_info=True)
            time.sleep(60)
            continue

        log.debug(f'Recieved response {messages}')
        if not messages:
            continue

        m = next(iter(messages))
        log.debug(f'Handling message with body {m.body}')
        payload = json.loads(m.body)
        log.debug(f'Parsed payload: {payload}')

        response_queue = sqs.Queue(payload['response_queue'])
        group_id = m.attributes['MessageGroupId']

        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
        }

        # Call homeassistant API
        ha_response = http.request(
            'POST', 
            request_url,
            headers=headers,
            body=payload['body'].encode('utf-8'),
        )
        response_payload = {
            'status': ha_response.status,
            'data': ha_response.data.decode('utf-8'),
            'group_id': group_id
        }
        log.debug(f'Sending response payload {response_payload}')
        if (ha_response.status != 200):
            log.warning(f'SQS Payload: {payload}')
            log.warning(f'Got HA response {response_payload}')

        message_body = json.dumps(response_payload)
        log.debug(f'Message response is {len(message_body)} bytes')
        message_body_hash = hashlib.sha256(message_body.encode('utf-8')).hexdigest()
        message_parts = split_string_for_sqs(message_body)
        log.debug(f'Sending reponse in {len(message_parts)} parts')
        for i in range(len(message_parts)):
            message_attributes = {
                'part_number': {
                    'StringValue': f'{i+1}',
                    'DataType': 'Number',
                },
                'total_parts': {
                    'StringValue': f'{len(message_parts)}',
                    'DataType': 'Number',
                }
            }
            deduplication_id = '-'.join([message_body_hash, group_id, str(i)])

            log.debug(f'Sending part {i}. Attributes: {message_attributes}, body size: {len(message_parts[i])} deduplication_id: {deduplication_id}')
            response_queue.send_message(MessageBody=message_parts[i], MessageGroupId=group_id, MessageDeduplicationId=deduplication_id, MessageAttributes=message_attributes)

        m.delete()

def split_string_for_sqs(s):
    chunks = []
    for i in range(0, len(s), MAX_MESSAGE_SIZE):
        chunks.append(s[i:i+MAX_MESSAGE_SIZE])
    return chunks

if __name__ == '__main__':
    with open('/data/options.json') as f:
        options = json.load(f)
        if (options.get("Debug") == True):
            log.setLevel(logging.DEBUG)
    loggable_options = dict(options)
    if ('AWS Secret Key' in loggable_options):
        loggable_options['AWS Secret Key'] = '*****'
    log.debug(f'Loaded options {loggable_options}')

    session = boto3.Session(
                        region_name=options['AWS Region'],
                        aws_access_key_id=options['AWS Access Key'],
                        aws_secret_access_key=options['AWS Secret Key'])

    stack_params = {
        'AlexaSkillId': options['Alexa Skill Id'],
        'Debug': str(options.get('Debug', False))
    }
    handle_cloudformation_stack(session, options['CloudFormation Stack Name'], stack_params=stack_params)
    poll_for_work(session,options)