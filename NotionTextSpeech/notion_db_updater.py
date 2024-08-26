import json
import os
from notion_client import Client
from notion_client.errors import APIResponseError

notion = Client(auth=os.environ['NOTION_API_KEY'])


def update_notion_entry(event):
    try:
        page_id = event['page_id']
        audio_url = event.get('audio_url')
        print(f"Updating Notion entry {page_id} with audio URL {audio_url}")
        if audio_url:
            properties={
                'Audio URL':{'url': audio_url},
                'Status': {'status': {'name': 'Completed'}},
                'Audio': {
                    'files': [
                        {
                        "name": "sentence.mp3",
                        "type": "external",
                        "external": {
                            "url": audio_url
                        }
                }
                ]}
            }
        try:
            notion.pages.update(
                page_id=page_id,
                properties=properties
            )
        except APIResponseError as e:
            print(f"Notion API error: {str(e)}")
            raise
        
        return {
            'statusCode': 200,
            'body': json.dumps('Notion database updated successfully')
        }
    except Exception as e:
        print(f"Error in update_notion_entry: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error: {str(e)}')
        }
