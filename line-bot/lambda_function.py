import json
import os
import boto3
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from langdetect import detect

# Initialize
LINE_CHANNEL_ACCESS_TOKEN = os.environ['LINE_CHANNEL_ACCESS_TOKEN']
LINE_CHANNEL_SECRET = os.environ['LINE_CHANNEL_SECRET']

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# Initialize AWS Bedrock
bedrock_runtime = boto3.client(
  service_name='bedrock-runtime',
  region_name='ap-northeast-1'
)

def is_japanese_text(text):
    return detect(text) == 'ja'

def generate_funny_response(user_message):
  try:
      is_japanese = is_japanese_text(user_message)
      
      request_body = {
          "inputText": f"""Create a short, funny and creative response about: {user_message}

          Rules:
          {f'- Respond ONLY in Japanese with crazy Japanese humor and slang 🇯🇵' if is_japanese else '- First in Japanese (max 25 words), then in English (max 25 words)'}
          - Use emojis
          - Be creative and absurd
          - IMPORTANT: Each language response must be under 25 words total
          - DO NOT include any introductory text""",
          "textGenerationConfig": {
              "maxTokenCount": 2048,
              "stopSequences": [],
              "temperature": 0.9,
              "topP": 0.8
          }
      }

      print(f"Bedrock request body: {json.dumps(request_body)}")

      response = bedrock_runtime.invoke_model(
          modelId='amazon.titan-text-express-v1',
          contentType='application/json',
          accept='application/json',
          body=json.dumps(request_body)
      )
      
      # Parse response - Updated to match actual response format
      response_body = json.loads(response['body'].read().decode())
      print(f"Bedrock response: {json.dumps(response_body)}")
      
      # Clean and validate response
      generated_text = response_body.get('results', [{}])[0].get('outputText', '').strip()
      
      # Remove everything before the first double newline
      if '\n\n' in generated_text:
          generated_text = generated_text.split('\n\n', 1)[1].strip()
      
      return generated_text.strip()
      
  except Exception as e:
      print(f"Error generating funny response: {str(e)}")
      return f"Even my joke generator is laughing too hard at '{user_message}' to make a proper joke! 😄"

def lambda_handler(event, context):
  print(f"Received event: {json.dumps(event)}")
  
  signature = event['headers'].get('x-line-signature', '')
  body = event['body']
  
  try:
      handler.handle(body, signature)
  except InvalidSignatureError:
      return {
          'statusCode': 400,
          'body': json.dumps('Invalid signature')
      }
  except Exception as e:
      print(f"Error in handler: {str(e)}")
      return {
          'statusCode': 500,
          'body': json.dumps('Internal server error')
      }
  
  return {
      'statusCode': 200,
      'body': json.dumps('OK')
  }

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
  try:
      user_message = event.message.text
      print(f"Received message: {user_message}")
      
      if not user_message:
          response = "I can't respond to an empty message. Try typing something! 😊"
      elif user_message.lower() == 'help':
          response = """🎭 Fun Bot Commands:
- Just type any word or message
- I'll generate a funny response!
- Type 'help' to see this message"""
      else:
          response = generate_funny_response(user_message)
      
      # Ensure response is not empty
      if not response or not response.strip():
          response = "Oops! Something went wrong. Let me tell you a default joke instead: Why don't programmers like nature? It has too many bugs! 🐛"
      
      print(f"Sending response: {response}")
      
      line_bot_api.reply_message(
          event.reply_token,
          TextSendMessage(text=response)
      )
      
  except LineBotApiError as line_error:
      print(f"LINE API Error: {str(line_error)}")
  except Exception as e:
      print(f"Error in handle_message: {str(e)}")