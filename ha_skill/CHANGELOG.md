# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),

## [1.0.7]
- Handle large responses by splitting the response across messages

## [1.0.6]
- Handle errors from calling SQS so addon doesn't die

## [1.0.5]
- Fix installation error

## [1.0.4]
- Add an option to enable debug logging for the addon and Lambda

## [1.0.3]
- Fix for debug setting in Lambda functions

## [1.0.2]
- Allow concurrent Alexa requests by dyanmically creating SQS queues

## [1.0.1]
- Fix for provision in new AWS accounts

## [1.0.0]
- Intial release
