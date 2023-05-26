# HA Skill
This addon is used to create an Alexa smart-home skill that doesn't require
HomeAssistant to be exposed to the internet. This is an alternative to
[HomeAssistant's official documentation for setting up Alexa](https://www.home-assistant.io/integrations/alexa.smart_home/).

This addon relies on Amazon SQS to send requests to the addon and the addon
makes requests to HomeAssistant using it owns credentials. Responses are 
sent back via SQS. All AWS resources are provisioned automatically using 
AWS CloudFormation. Manual setup is still required to create a custom Alexa 
Skill and to create an AWS account and create bootstrap IAM credentials.

## Setup

### Create an AWS Account
https://aws.amazon.com/free/

All account usage will fit in the [always free tier](https://aws.amazon.com/free/?awsf.Free%20Tier%20Types=tier%23always-free)

### Create an Alexa Skill

Follow the instructions for [Create an Amazon Alexa Smart Home Skill](https://www.home-assistant.io/integrations/alexa.smart_home/#create-an-amazon-alexa-smart-home-skill).

Stop when you get to **Create an AWS Lambda Function**


### Install and run HA Skill

**Install the addon**

**Configure the addon**
* Create an IAM user in the AWS Console and attach the following inline policy. **Warning**: This user effectivly has full access to your AWS account due to `iam:*` permissions.
```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "HASkillBootstrap",
            "Effect": "Allow",
            "Action": [
                "iam:*",
                "lambda:*",
                "sqs:*",
                "cloudformation:*",
                "logs:*"
            ],
            "Resource": "*"
        }
    ]
}
```

Use the `Access Key Id` and `Secret Access Key` of the IAM user you created in the configuration for the addon.

Select the appropraite region for where your Alexa skill is located
* `us-east-1` for English (US) or English (CA) skills
* `eu-east-1` for English (UK), English (IN), German (DE), Spanish (ES) or French (FR) skills
* `us-west-2` for for Japanese and English (AU) skills.

Fill in your `Alexa Skill Id` from when you setup the skill before

Start the addon

The addon will provision the necessary AWS resources for connecting Alexa to your Home Assistant

View the logs to retrieve the 
* `AlexaEndpoint`
* `AccessTokenUri`
* `AuthorizationUri`
These will be used for configuring Account Linking of your Alexa skill

### Finish Alexa Skill Setup

Follow the instructions for [Configure the Smart Home Service Endpoint](https://www.home-assistant.io/integrations/alexa.smart_home/#configure-the-smart-home-service-endpoint). Use the `AlexaEndpoint` from above. 

Follow the instuctions for [Account Linking](https://www.home-assistant.io/integrations/alexa.smart_home/#account-linking).

* For `Authorization URI` use the `AuthorizationUri` that you saved from the logs above
* For `Access Token URI`: use `AccessTokenUri`

For additional setup / configuration options for making specific entities in HomeAssistant available in Alexa, see the [official documentation](https://www.home-assistant.io/integrations/alexa.smart_home/#alexa-smart-home-component-configuration).

**Note:** Initial device discovery may error in the app but devices are still discovered