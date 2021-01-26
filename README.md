# sns2slack

Amazon Lambda function (Python 3.7) for Amazon SNS to send notifications to Slack.

## required environment variables

- `KMS_ENCRYPTED_HOOK_URL` or `HOOK_URL`
- `SLACK_CHANNEL`

## deploy

using [rackerlabs/lambda\-uploader](https://github.com/rackerlabs/lambda-uploader).

```
pip install -r requirements-dev.txt
cp config-example.mk
vi config.mk
vi lambda-xxx.json
make deploy
```

or copy and paste!

## repository

- https://github.com/hirose31/sns2slack
