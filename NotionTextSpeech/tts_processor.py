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

def check_dynamodb(french_text):
    try:
        response = table.get_item(Key={'french_text': french_text})
        return response.get('Item')
    except ClientError as e:
        print(f"Error checking DynamoDB: {str(e)}")
        return None

def insert_dynamodb(french_text, english_text, sample_sentence, audio_url):
    try:
        table.put_item(
            Item={
                'french_text': french_text,
                'english_text': english_text,
                'sample_sentence': sample_sentence,
                'audio_url': audio_url
            },
            ConditionExpression='attribute_not_exists(french_text)'
        )
        print(f"Successfully inserted into DynamoDB: {french_text}")
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            print(f"Redundant french_text detected: {french_text}")
            return False
        else:
            print(f"Error inserting into DynamoDB: {str(e)}")
            raise

def generate_audio(french_text):
    try:
        response = polly.synthesize_speech(Text=french_text, OutputFormat='mp3', VoiceId='Mathieu')
        key = f"audio_{hash(french_text)}.mp3"
        s3.put_object(Bucket=BUCKET_NAME, Key=key, Body=response['AudioStream'].read())
        audio_url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{key}"
        return audio_url
    except ClientError as e:
        print(f"Error generating audio: {str(e)}")
        raise

def process_french_text(event):
    try:
        page_id = event['page_id']
        french_text = event['french_text']
        english_text = "English Dumy"
        sample_sentence = "dumydumydumy"
        print(f"Processing page {page_id}: {french_text}, {sample_sentence}")

        # Check DynamoDB for existing record
        existing_record = check_dynamodb(french_text)

        if existing_record:
            print(f"Found existing record for: {french_text}")
            audio_url = existing_record['audio_url']
            english_text = existing_record['english_text']
            sample_sentence = existing_record['sample_sentence']
        else:
            print(f"Generating new audio for: {french_text}")
            audio_url = generate_audio(french_text)
            insert_success = insert_dynamodb(french_text, english_text, sample_sentence, audio_url)
            if not insert_success:
                # Handle the case where the item wasn't inserted due to redundancy
                existing_record = check_dynamodb(french_text)
                if existing_record:
                    audio_url = existing_record['audio_url']
                    english_text = existing_record['english_text']
                    sample_sentence = existing_record['sample_sentence']
                else:
                    raise Exception("Failed to insert or retrieve redundant french_text")

        # Update Notion
        return update_notion_entry({
            'page_id': page_id,
            'audio_url': audio_url,
            'french_text': french_text,
            'english_text': english_text,
            'sample_sentence': sample_sentence,
            'status': 'Completed'
        })

    except Exception as e:
        print(f"Error in process_french_text: {str(e)}")
        return update_notion_entry({'page_id': page_id, 'status': f'Error'})
