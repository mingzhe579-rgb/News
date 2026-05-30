import os
import json
from datetime import datetime
import requests
from google.oauth2.service_account import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Configuration
NEWSAPI_KEY = os.getenv('NEWSAPI_KEY')
SHEET_ID = os.getenv('SHEET_ID')
SERVICE_ACCOUNT_JSON = os.getenv('SERVICE_ACCOUNT_JSON')

# Topic mappings for news queries
TOPICS = {
    'ai': 'artificial intelligence',
    'singapore': 'Singapore',
    'benefits': 'AI benefits innovation',
    'harms': 'AI risks job displacement'
}

def get_news():
    """Fetch news from NewsAPI"""
    all_news = []
    
    for topic_key, query in TOPICS.items():
        url = 'https://newsapi.org/v2/everything'
        params = {
            'q': query,
            'sortBy': 'publishedAt',
            'language': 'en',
            'pageSize': 3,  # Get top 3 per topic
            'apiKey': NEWSAPI_KEY
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            articles = response.json().get('articles', [])
            
            for article in articles:
                all_news.append({
                    'date': datetime.now().strftime('%Y-%m-%d'),
                    'title': article.get('title', 'N/A')[:100],
                    'topic': topic_key,
                    'summary': article.get('description', 'N/A')[:200],
                    'source': article.get('source', {}).get('name', 'News'),
                    'url': article.get('url', '')
                })
        except Exception as e:
            print(f"Error fetching {topic_key}: {e}")
    
    return all_news

def update_sheet(news_items):
    """Add news items to Google Sheet"""
    
    # Set up credentials
    creds_dict = json.loads(SERVICE_ACCOUNT_JSON)
    credentials = Credentials.from_service_account_info(creds_dict, scopes=['https://www.googleapis.com/auth/spreadsheets'])
    
    service = build('sheets', 'v4', credentials=credentials)
    
    # Prepare values for insertion
    values = []
    for item in news_items:
        values.append([
            item['date'],
            item['title'],
            item['topic'],
            item['summary'],
            item['source'],
            item['url']
        ])
    
    # Append to sheet (skip header row)
    body = {'values': values}
    
    try:
        result = service.spreadsheets().values().append(
            spreadsheetId=SHEET_ID,
            range='Sheet1!A2',
            valueInputOption='RAW',
            body=body
        ).execute()
        print(f"✅ Added {result.get('updates', {}).get('updatedRows', 0)} rows to sheet")
    except Exception as e:
        print(f"❌ Error updating sheet: {e}")

if __name__ == '__main__':
    print("🔄 Fetching news...")
    news = get_news()
    print(f"✅ Found {len(news)} articles")
    
    print("📝 Updating Google Sheet...")
    update_sheet(news)
    print("✅ Done!")
