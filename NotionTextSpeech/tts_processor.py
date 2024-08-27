import boto3
import json
import os
from botocore.exceptions import ClientError
from notion_db_updater2 import update_notion_entry

# AWS Configuration
AWS_PROFILE = 'ko-engineer'
AWS_REGION = 'ap-northeast-1'
BUCKET_NAME = os.environ['S3_BUCKET_NAME']
DYNAMODB_TABLE_NAME = 'FrenchAudioCache'

# Create a session with the specified profile and region
session = boto3.Session(profile_name=AWS_PROFILE, region_name=AWS_REGION)

# Use the session to create clients
s3 = session.client('s3')
polly = session.client('polly')
dynamodb = session.resource('dynamodb')
table = dynamodb.Table(DYNAMODB_TABLE_NAME)

# Create a Bedrock client
bedrock = session.client('bedrock-runtime')


def get_or_create_dynamodb_item(french_text, english_text, sample_sentence, audio_url):
    try:
        # Attempt to add a new item. If it already exists, update it.
        response = table.update_item(
            Key={'french_text': french_text},
            UpdateExpression='SET english_text = :e, sample_sentence = :s, audio_url = :a',
            ExpressionAttributeValues={
                ':e': english_text,
                ':s': sample_sentence,
                ':a': audio_url
            },
            ReturnValues='ALL_NEW'
        )
        return response['Attributes']
    except ClientError as e:
        print(f"Error in get_or_create_dynamodb_item: {str(e)}")
        raise

def generate_audio(sample_sentence):
    try:
        response = polly.synthesize_speech(Text=sample_sentence, OutputFormat='mp3', VoiceId='Mathieu')
        key = f"audio_{hash(sample_sentence)}.mp3"
        s3.put_object(Bucket=BUCKET_NAME, Key=key, Body=response['AudioStream'].read())
        audio_url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{key}"
        return audio_url
    except ClientError as e:
        print(f"Error generating audio: {str(e)}")
        raise

# Function to generate sample sentences using AWS Bedrock
def generate_sample_sentence(french_text):
    try:
        prompt = f"""Human: You are a French language expert. Generate a sample sentence in French using the following word or phrase: "{french_text}". 
        The sentence should be natural, contextually appropriate, and demonstrate the usage of the given word or phrase. 
        Provide only the French sentence without any additional explanation.

        Assistant: Here's a sample sentence in French using "{french_text}":

        Human: Thank you. Now, please provide only the generated French sentence, without any additional text.

        Assistant: """

        body = json.dumps({
            "prompt": prompt,
            "max_tokens_to_sample": 300,
            "temperature": 0.7,
            "top_p": 0.95,
        })

        response = bedrock.invoke_model(
            modelId="anthropic.claude-v2:1",
            body=body
        )

        response_body = json.loads(response['body'].read())
        sample_sentence = response_body['completion'].strip()
        return sample_sentence
    except Exception as e:
        print(f"Error generating sample sentence: {str(e)}")
        return None

def translate_to_english(french_text):
    try:
        prompt = f"""Human: Translate the following French text to English: "{french_text}".
        Provide only the English translation without any additional explanation.

        Assistant: Here's the English translation:

        Human: Thank you. Now, please provide only the English translation, without any additional text.

        Assistant: """

        body = json.dumps({
            "prompt": prompt,
            "max_tokens_to_sample": 300,
            "temperature": 0.3,
            "top_p": 0.95,
        })

        response = bedrock.invoke_model(
            modelId="anthropic.claude-v2:1",
            body=body
        )

        response_body = json.loads(response['body'].read())
        english_translation = response_body['completion'].strip()
        return english_translation
    except Exception as e:
        print(f"Error translating to English: {str(e)}")
        return None

def process_french_text(event):
    try:
        page_id = event.get('page_id')
        french_text = event.get('french_text')

        if not page_id or not french_text:
            raise ValueError("Missing required fields: page_id or french_text")

        # First, check if the item already exists in DynamoDB
        existing_item = table.get_item(Key={'french_text': french_text}).get('Item', {})

        if existing_item:
            print(f"Found existing record for: {french_text}")
            audio_url = existing_item.get('audio_url')
            english_text = existing_item.get('english_text')
            sample_sentence = existing_item.get('sample_sentence')
        else:
            print(f"Generating new content for: {french_text}")
            # Generate audio, sample sentence, and translation
            sample_sentence = generate_sample_sentence(french_text)
            english_text = translate_to_english(french_text)
            audio_url = generate_audio(sample_sentence)

        # Validate generated content
        if not english_text:
            raise ValueError("Failed to generate English translation")
        if not sample_sentence:
            raise ValueError("Failed to generate sample sentence")
        if not audio_url:
            raise ValueError("Failed to generate audio URL")

        # Always call get_or_create_dynamodb_item to ensure the item is in DynamoDB
        item = get_or_create_dynamodb_item(french_text, english_text, sample_sentence, audio_url)
        print(f"Processed: {french_text}, {english_text}, {sample_sentence}, {audio_url}")

        # Update Notion
        return update_notion_entry({
            'page_id': page_id,
            'audio_url': item.get('audio_url'),
            'french_text': item.get('french_text'),
            'english_text': item.get('english_text'),
            'sample_sentence': item.get('sample_sentence'),
            'audio_status': 'Completed'
        })
    except ValueError as ve:
        print(f"Validation error in process_french_text: {str(ve)}")
        return update_notion_entry({'page_id': page_id, 'audio_status': 'Error'})
    except Exception as e:
        print(f"Error in process_french_text: {str(e)}")
        return update_notion_entry({'page_id': page_id, 'audio_status': 'Error'})
