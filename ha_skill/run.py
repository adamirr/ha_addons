import boto3
import botocore
import json
import logging
import os
import requests
import sys
import urllib3
import uuid

logging.basicConfig(
    format='%(asctime)s %(levelname)-6s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S'
)
log = logging.getLogger('ha-skill')

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


def poll_for_work(session):
    sqs = session.resource('sqs')
    request_queue = sqs.get_queue_by_name(QueueName=QUEUE_NAME)

    http = urllib3.PoolManager(
        timeout=urllib3.Timeout(connect=2.0, read=5.0)
    )

    log.debug(f'Environment: {os.environ}')
    token = os.environ.get('SUPERVISOR_TOKEN')
    assert token is not None

    log.info(f'Polling for work from {QUEUE_NAME}...')
    while True:
        messages = request_queue.receive_messages(MaxNumberOfMessages=1, AttributeNames=['MessageGroupId'])
        log.debug(f'Recieved response {messages}')
        if not messages:
            continue

        m = next(iter(messages))
        log.debug(f'Handling message with body {m.body}')
        payload = json.loads(m.body)
        log.debug(f'Parsed payload: {payload}')

        response_queue = sqs.Queue(payload['response_queue'])
        group_id = m.attributes['MessageGroupId']

        request_url = 'http://supervisor/core/api/alexa/smart_home'
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

        response_queue.send_message(MessageBody=json.dumps(response_payload), MessageGroupId=group_id)
        m.delete()

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
    poll_for_work(session)