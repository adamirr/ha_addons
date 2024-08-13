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

## Docker standalone mode
If you want to use this addon, but you are running HomeAssistant as a Docker container, you can do the following steps:
1. Create a Long Lived Access Token in HomeAssistant
1. Clone this repo
1. `cd ha_addons/ha_skill/`
1. Rename the `example-options.json` file to `options.json` and paste in your informations
1. You can start the container with: `docker compose up -d`
