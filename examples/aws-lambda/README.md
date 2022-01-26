# What is this?

This is an example [opta](https://github.com/run-x/opta) configuration file to deploy a simple lambda function on AWS that handles API calls from the internet.

# What does this do?
It deploys a simple [python lambda function](https://github.com/awsdocs/aws-doc-sdk-examples/blob/main/python/example_code/lambda/lambda_handler_rest.py) with AWS API Gateway. It also sets up various other resources like VPCs, subnets.

# Steps to deploy
1. Fill in the following required variables in the [config](opta.yaml) file
  * org_name
  * account_id
2. Create a zip file for your lambda.
```bash
zip my-deployment-package.zip lambda_function.py
```
3. Run `opta apply`
This will create all the required resources in your AWS account and deploy your lambda.

That's it. AWS lambda is deployed. You will see an output like this.

```
cloudwatch_log_group_name = "/aws/lambda/opta-lambdafunction-b0bf"
cloudwatch_log_group_url = "https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#logsV2:log-groups/log-group/%2Faws%2Flambda%2Fopta-lambdafunction-b0bf"
function_arn = "arn:aws:lambda:us-east-1:828259620284:function:opta-lambdafunction-b0bf"
function_name = "opta-lambdafunction-b0bf"
kms_account_key_arn = "arn:aws:kms:us-east-1:828259620284:key/3a802e75-7f6f-4217-aabf-45ca0b7d9e37"
kms_account_key_id = "3a802e75-7f6f-4217-aabf-45ca0b7d9e37"
lambda_trigger_uri = "https://43neawor1c.execute-api.us-east-1.amazonaws.com/"
private_subnet_ids = [
  "subnet-0dd60ec42b37cd11b",
  "subnet-03ff99b7c866be1ff",
  "subnet-01c2d9c9c9a0f2d47",
]
```

You can test the deployment using curl like:

```bash
curl -H "day: day" https://43neawor1c.execute-api.us-east-1.amazonaws.com
```
make sure to replace the uri with the uri generated for you. And you should see an output like:

```
{"message": "Got your GET, D. E. Fault. Have a nice day!", "input": {"version": "2.0", "routeKey": "ANY /", "rawPath": "/", "rawQueryString": "", "headers": {"accept": "*/*", "content-length": "0", "day": "day", "host": "43neawor1c.execute-api.us-east-1.amazonaws.com", "user-agent": "curl/7.77.0", "x-amzn-trace-id": "Root=1-61d8bc57-705914ce514abef9631be62a", "x-forwarded-for": "73.162.24.47", "x-forwarded-port": "443", "x-forwarded-proto": "https"}, "requestContext": {"accountId": "828259620284", "apiId": "43neawor1c", "domainName": "43neawor1c.execute-api.us-east-1.amazonaws.com", "domainPrefix": "43neawor1c", "http": {"method": "GET", "path": "/", "protocol": "HTTP/1.1", "sourceIp": "73.162.24.47", "userAgent": "curl/7.77.0"}, "requestId": "LmJduiNOIAMEMkA=", "routeKey": "ANY /", "stage": "$default", "time": "07/Jan/2022:22:19:03 +0000", "timeEpoch": 1641593943604}, "isBase64Encoded": false}}%
```

You can also visit the `lambda_trigger_uri` in your browser to check your rest api deployed on lambda.

# References
* Checkout [AWS docs](https://docs.aws.amazon.com/lambda/latest/dg/python-package.html) on how to package more complex lambdas
* [Opta docs](https://docs.opta.dev)

For more guidance, please reach out to us in our [slack channel](https://slack.opta.dev).
