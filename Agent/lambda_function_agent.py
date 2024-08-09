import json
import boto3
from botocore.exceptions import ClientError

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('koagentdydb')

def lambda_handler(event, context):
    try:
        # This is the command getting the invoke from Test-Config.
        # account_id = event['account_id']
        # This doc gives the structure of the event from bedrock.
        # https://docs.aws.amazon.com/bedrock/latest/userguide/agents-lambda.html
        account_id = event['parameters'][0]['value']
        print(account_id)

        # Create a request syntax to retrieve data from the DynamoDB Table using GET Item method
        # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb/client/get_item.html
        response = table.get_item(
            Key={
                'accountid': account_id
            }
        )
        print(response)

        # Format the response as per the requirement of Bedrock Agent Action Group
        # https://docs.aws.amazon.com/bedrock/latest/userguide/agents-lambda.html
        response_body = {
            'application/json': {
                'body': json.dumps(response)
            }
        }

        action_response = {
            'actionGroup': event['actionGroup'],
            'apiPath': event['apiPath'],
            'httpMethod': event['httpMethod'],
            'httpStatusCode': 200,
            'responseBody': response_body
        }

        session_attributes = event['sessionAttributes']
        prompt_session_attributes = event['promptSessionAttributes']

        api_response = {
            'messageVersion': '1.0',
            'response': action_response,
            'sessionAttributes': session_attributes,
            'promptSessionAttributes': prompt_session_attributes
        }

        return api_response

    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        print(f"DynamoDB error: {error_code} - {error_message}")

        # Return an error response
        return {
            'messageVersion': '1.0',
            'response': {
                'actionGroup': event['actionGroup'],
                'apiPath': event['apiPath'],
                'httpMethod': event['httpMethod'],
                'httpStatusCode': 500,
                'responseBody': {
                    'application/json': {
                        'body': json.dumps({
                            'error': error_message
                        })
                    }
                }
            },
            'sessionAttributes': event['sessionAttributes'],
            'promptSessionAttributes': event['promptSessionAttributes']
        }

    except Exception as e:
        print(f"Unexpected error: {e}")

        # Return a generic error response
        return {
            'messageVersion': '1.0',
            'response': {
                'actionGroup': event['actionGroup'],
                'apiPath': event['apiPath'],
                'httpMethod': event['httpMethod'],
                'httpStatusCode': 500,
                'responseBody': {
                    'application/json': {
                        'body': json.dumps({
                            'error': 'An unexpected error occurred.'
                        })
                    }
                }
            },
            'sessionAttributes': event['sessionAttributes'],
            'promptSessionAttributes': event['promptSessionAttributes']
        }