# HA Skill
This addon is used to create an Alexa smart-home skill that doesn't require
HomeAssistant to be exposed to the internet. This is an alternative to
[HomeAssistant's official documentation for setting up Alexa](https://www.home-assistant.io/integrations/alexa.smart_home/).

This addon relies on Amazon SQS to send requests to the addon and the addon
makes requests to HomeAssistant using it owns credentials. Responses are 
sent back via SQS. All AWS resources are provisioned automatically using 
AWS CloudFormation. Manual setup is still required to create a custom Alexa 
Skill and to create an AWS account and create bootstrap IAM credentials. All AWS
usage will fit in the [always free tier](https://aws.amazon.com/free/?awsf.Free%20Tier%20Types=tier%23always-free).

See DOCS.md for setup instructions.