import boto3
import json
import os
from botocore.exceptions import ClientError
from notion_db_updater import update_notion_entry

# AWS Configuration
AWS_PROFILE = 'ko-engineer'  # Replace with your actual profile name
AWS_REGION = 'ap-northeast-1'  # This is already specified for Polly, but we'll use it for S3 as well
BUCKET_NAME = os.environ['S3_BUCKET_NAME']

# Create a session with the specified profile and region
session = boto3.Session(profile_name=AWS_PROFILE, region_name=AWS_REGION)

# Use the session to create clients
s3 = session.client('s3')
polly = session.client('polly')

def generate_audio(event):
    try:
        page_id = event['page_id']
        french_text = event['french_text']
        print(f"Processing page {page_id}: {french_text}")
        
        # Generate audio using Polly
        try:
            response = polly.synthesize_speech(Text=french_text, OutputFormat='mp3', VoiceId='Mathieu')
        except ClientError as e:
            print(f"Error with Polly: {str(e)}")
            raise
        
        # Upload to S3
        key = f"audio_{page_id}.mp3"
        try:
            s3.put_object(Bucket=BUCKET_NAME, Key=key, Body=response['AudioStream'].read())
        except ClientError as e:
            print(f"Error uploading to S3: {str(e)}")
            raise
        
        # Generate S3 URL
        audio_url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{key}"
        
        # Call Notion update function
        return update_notion_entry({'page_id': page_id, 'audio_url': audio_url, 'french_text': french_text})
    except Exception as e:
        print(f"Error in generate_audio: {str(e)}")
        return update_notion_entry({'page_id': page_id, 'status': 'Error'})
