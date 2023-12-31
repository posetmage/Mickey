import os
import asyncio
import json
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

async def set_text_async(document_id, text_to_set):
    creds = Credentials.from_service_account_file('get-survey-c8bf2f366d30.json', scopes=[
        'https://www.googleapis.com/auth/documents',
        'https://www.googleapis.com/auth/drive'
    ])
    service = build('docs', 'v1', credentials=creds)

    document = service.documents().get(documentId=document_id).execute()
    end_index = document['body']['content'][-1]['endIndex']

    # Requests to delete the content and set new content
    requests = [
        # Delete existing content
        {
            'deleteContentRange': {
                'range': {
                    'startIndex': 1,
                    'endIndex': end_index-1
                }
            }
        },
        # Insert new content
        {
            'insertText': {
                'location': {
                    'index': 1
                },
                'text': text_to_set
            }
        }
    ]

    service.documents().batchUpdate(documentId=document_id, body={'requests': requests}).execute()

async def get_document_content_async(document_id):
    creds = Credentials.from_service_account_file('get-survey-c8bf2f366d30.json', scopes=[
        'https://www.googleapis.com/auth/documents',
        'https://www.googleapis.com/auth/drive'
    ])
    service = build('docs', 'v1', credentials=creds)
    document = service.documents().get(documentId=document_id).execute()
    content = ""
    for item in document['body']['content']:
        if 'paragraph' in item:
            for element in item['paragraph']['elements']:
                content += element.get('textRun', {}).get('content', '')
    return content

def lambda_handler(event, context):
    headers = {
        'Access-Control-Allow-Headers': 'content-type',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,HEAD',
        'Access-Control-Allow-Credentials' : True
    }

    # Preflight request. Reply successfully:
    if event['httpMethod'] == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': 'preflight successful'
        }

    # Handling GET request
    if event['httpMethod'] == 'GET':
        document_id = event.get('queryStringParameters', {}).get('document_id', None)
        if not document_id:
            print("No 'document_id' provided")
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps("No 'document_id' provided in the request")
            }
        loop = asyncio.get_event_loop()
        document_content = loop.run_until_complete(get_document_content_async(document_id))
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({"content": document_content})
        }

    # Check if 'body' is in the event and try to extract 'text' and 'document_id'
    if 'body' not in event:
        print("No 'body' in event")
        return {
            'statusCode': 400,
            'headers': headers,
            'body': json.dumps('No body provided in the request')
        }
    else:
        body = json.loads(event['body'])
        if 'text' not in body or 'document_id' not in body:
            print("No 'text' or 'document_id' in body")
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps('No text or document_id provided in the request body')
            }
        else:
            text_to_append = body['text']
            document_id = body['document_id']
            loop = asyncio.get_event_loop()
            loop.run_until_complete(set_text_async(document_id, text_to_append))

            message = "Text added to Google Doc file"
            print(message)
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps(message)
            }
