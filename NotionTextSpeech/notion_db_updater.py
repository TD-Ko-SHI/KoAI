import json
import os
from notion_client import Client
from notion_client.errors import APIResponseError

notion = Client(auth=os.environ['NOTION_API_KEY'])

def update_notion_entry(event):
    try:
        page_id = event['page_id']
        french_text = event['french_text']
        english_text = event['english_text']
        sample_sentence = event['sample_sentence']
        audio_url = event['audio_url']
        the_status = event['status']
        print(f"page_info: {page_id}, {french_text}, {english_text}, {sample_sentence}, {audio_url}, {the_status}")

        properties = {
            'French': {'rich_text': [{'text': {'content': french_text}}]},
            'English': {'rich_text': [{'text': {'content': english_text}}]},
            'Sample Sentence': {'rich_text': [{'text': {'content': sample_sentence}}]},
            'Status': {'status': {'name': the_status}},
        }

        if audio_url:
            properties['Audio'] = {
                'files': [
                    {
                        "name": "sentence.mp3",
                        "type": "external",
                        "external": {
                            "url": audio_url
                        }
                    }
                ]
            }

        try:
            notion.pages.update(
                page_id=page_id,
                properties=properties
            )
            print(f"Successfully updated Notion page {page_id}")
            return {
                'statusCode': 200,
                'body': json.dumps('Notion database updated successfully')
            }
        except APIResponseError as e:
            print(f"Notion API error: {str(e)}")
            return {
                'statusCode': 400,
                'body': json.dumps(f'Notion API Error: {str(e)}')
            }
        
    except KeyError as e:
        print(f"Missing required field: {str(e)}")
        return {
            'statusCode': 400,
            'body': json.dumps(f'Missing required field: {str(e)}')
        }
    except Exception as e:
        print(f"Error in update_notion_entry: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error: {str(e)}')
        }