import os
import json
import base64
import hmac
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get LINE Channel Secret from environment variable
CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')
if not CHANNEL_SECRET:
  raise ValueError("Please set LINE_CHANNEL_SECRET in .env file")

def generate_test_payload():
  # Create test event body
  test_event = {
      "destination": "Ue197534f68e9...",
      "events": [{
          "type": "message",
          "message": {
              "type": "text",
              "id": "1234567890",
              "text": "Hello, bot!"
          },
          "timestamp": 1462629479859,
          "source": {
              "type": "user",
              "userId": "U4af4980629..."
          },
          "replyToken": "nHuyWiB7yP5Zw52FIkcQobQuGDXCTA",
          "mode": "active"
      }]
  }
  
  # Convert body to JSON string
  body = json.dumps(test_event)
  
  # Generate signature
  hash = hmac.new(
      CHANNEL_SECRET.encode('utf-8'),
      body.encode('utf-8'),
      'sha256'
  ).digest()
  signature = base64.b64encode(hash).decode('utf-8')
  
  # Create Lambda test event
  lambda_test_event = {
      "headers": {
          "x-line-signature": signature,
          "x-line-request-id": "12345678-1234-1234-1234-123456789012"
      },
      "body": body
  }
  
  return lambda_test_event

def main():
  # Generate test payload
  test_event = generate_test_payload()
  
  # Save to file
  with open('lambda_test_event.json', 'w') as f:
      json.dump(test_event, f, indent=2)
  
  print("Test event has been saved to 'lambda_test_event.json'")
  print("\nGenerated signature:", test_event['headers']['x-line-signature'])
  print("\nYou can use this payload in Lambda test console")

if __name__ == "__main__":
  main()