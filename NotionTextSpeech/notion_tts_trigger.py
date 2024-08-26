import json
import os
from dotenv import load_dotenv
from notion_client import Client
from tts_processor import generate_audio
from notion_db_updater import update_notion_entry

notion = Client(auth=os.environ['NOTION_API_KEY'])
DATABASE_ID = os.environ['NOTION_DATABASE_ID']


def lambda_handler(event, context):
    try:
        results = notion.databases.query(
            database_id=DATABASE_ID,
            filter={
                "property": "Status",
                "status": {"equals": "Not Started"}
            }
        )
        
        print(results)
        
        processed_count = 0
        for page in results['results']:
            try:
                page_id = page['id']
                print(page_id)
                french_text = page['properties']['French']['rich_text'][0]['text']['content']
                print(page['properties'])
                # Update status to "Processing"
                notion.pages.update(
                    page_id=page_id,
                    properties={
                        'Status': {'status': {'name': 'Processing'}}
                    }
                )
                
                # Directly call the generate_audio function
                generate_audio({'page_id': page_id, 'french_text': french_text})
                processed_count += 1
            except Exception as e:
                print(f"Error processing page {page_id}: {str(e)}")
                notion.pages.update(
                    page_id=page_id,
                    properties={
                        'Status': {'select': {'name': 'Error'}}
                    }
                )
        
        return {
            'statusCode': 200,
            'body': json.dumps(f'Processed {processed_count} pages')
        }
    except Exception as e:
        print(f"Error in process_notion_entries: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error: {str(e)}')
        }

# For local debugging
if __name__ == "__main__":
    event = {}
    context = {}
    lambda_handler(event, context)