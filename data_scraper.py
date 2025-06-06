import tweepy
import pandas as pd
import requests
import json
import time
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import pytz 

# Load environment variables
load_dotenv()

# Define a global or class-level variable to track Twitter rate limit resets
TWITTER_LAST_RATE_LIMIT_HIT = None

class SocialMediaScraper:
    """
    Scraper for collecting data from Twitter, Reddit, and YouTube
    Note: This requires API keys to be set in .env file
    """
    
    def __init__(self):
        # self.twitter_api = self.setup_twitter_api() # Commented out Twitter API setup
        self.twitter_api = None # Explicitly set to None as we're skipping Twitter
        self.reddit_headers = {'User-Agent': 'sentiment-analyzer/1.0'}
        
    def setup_twitter_api(self):
        '''Setup Twitter API connection'''
        try:
            bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
            if bearer_token:
                return tweepy.Client(bearer_token=bearer_token, wait_on_rate_limit=True) 
            else:
                print("Twitter Bearer Token not found. Please set TWITTER_BEARER_TOKEN in .env file")
                return None
        except Exception as e:
            print(f"Error setting up Twitter API: {e}")
            return None
    
    def scrape_twitter_data(self, query, max_tweets=10): 
        '''Scrape tweets related to government policies'''
        # This method is now effectively disabled by the __init__ change,
        # but kept for completeness if you uncomment it later.
        if not self.twitter_api:
            print("Twitter API not configured or explicitly skipped.")
            return pd.DataFrame()
        
        global TWITTER_LAST_RATE_LIMIT_HIT

        if TWITTER_LAST_RATE_LIMIT_HIT and (time.time() - TWITTER_LAST_RATE_LIMIT_HIT < 900): # 15 minutes
            print("Twitter API recently hit rate limit. Skipping Twitter scraping for now to avoid long waits.")
            return pd.DataFrame()

        try:
            tweets_data = []
            
            tweets = tweepy.Paginator(
                self.twitter_api.search_recent_tweets,
                query=query,
                tweet_fields=['created_at', 'author_id', 'public_metrics', 'geo'],
                max_results=min(max_tweets, 100) 
            ).flatten(limit=max_tweets)
            
            for tweet in tweets:
                if tweet and tweet.created_at and tweet.text:
                    tweets_data.append({
                        'date': tweet.created_at, 
                        'text': tweet.text,
                        'platform': 'Twitter',
                        'likes': tweet.public_metrics['like_count'] if tweet.public_metrics else 0,
                        'shares': tweet.public_metrics['retweet_count'] if tweet.public_metrics else 0,
                        'author_id': tweet.author_id
                    })
            
            return pd.DataFrame(tweets_data)
            
        except tweepy.TooManyRequests as e:
            print(f"Twitter API Rate Limit Exceeded (429): {e}. Setting a flag to pause future Twitter requests.")
            TWITTER_LAST_RATE_LIMIT_HIT = time.time() 
            return pd.DataFrame()
        except tweepy.TweepyException as e:
            print(f"Error scraping Twitter data: {e}")
            return pd.DataFrame()
        except Exception as e: 
            print(f"An unexpected error occurred during Twitter scraping: {e}")
            return pd.DataFrame()
    
    def scrape_reddit_data(self, subreddit, query, limit=20): 
        """Scrape Reddit comments and posts"""
        try:
            posts_data = []
            
            url = f"https://www.reddit.com/r/{subreddit}/search.json"
            params = {
                'q': query,
                'sort': 'new',
                'limit': limit,
                'restrict_sr': 'on'
            }
            
            response = requests.get(url, headers=self.reddit_headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                
                for post in data['data']['children']:
                    post_data = post['data']
                    posts_data.append({
                        'date': datetime.fromtimestamp(post_data['created_utc']), 
                        'text': post_data['title'] + ' ' + post_data.get('selftext', ''),
                        'platform': 'Reddit',
                        'likes': post_data['ups'],
                        'shares': post_data['num_comments'],
                        'subreddit': subreddit
                    })
            elif response.status_code == 429:
                print(f"Reddit API Rate Limit Exceeded (429). Will try again later.")
                return pd.DataFrame()
            else:
                print(f"Error scraping Reddit data: Status Code {response.status_code} - {response.text}")
                return pd.DataFrame()
            
            return pd.DataFrame(posts_data)
            
        except Exception as e:
            print(f"Error scraping Reddit data: {e}")
            return pd.DataFrame()
    
    def scrape_youtube_comments(self, video_id, max_comments=10): 
        """Scrape YouTube comments (requires YouTube API key)"""
        try:
            api_key = os.getenv('YOUTUBE_API_KEY')
            if not api_key:
                print("YouTube API key not found. Please set YOUTUBE_API_KEY in .env file")
                return pd.DataFrame()
            
            comments_data = []
            
            url = "https://www.googleapis.com/youtube/v3/commentThreads"
            params = {
                'part': 'snippet',
                'videoId': video_id,
                'key': api_key,
                'maxResults': min(max_comments, 100),
                'order': 'time'
            }
            
            response = requests.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                
                for item in data.get('items', []):
                    comment = item['snippet']['topLevelComment']['snippet']
                    comments_data.append({
                        'date': pd.to_datetime(comment['publishedAt']), 
                        'text': comment['textOriginal'],
                        'platform': 'YouTube',
                        'likes': comment['likeCount'],
                        'shares': 0,    
                        'author': comment['authorDisplayName']
                    })
            elif response.status_code == 429:
                print(f"YouTube API Rate Limit Exceeded (429). Will try again later.")
                return pd.DataFrame()
            else:
                print(f"Error scraping YouTube data: Status Code {response.status_code} - {response.text}")
                return pd.DataFrame()
            
            return pd.DataFrame(comments_data)
            
        except Exception as e:
            print(f"Error scraping YouTube data: {e}")
            return pd.DataFrame()
    
    def scrape_policy_data(self, policy_name, days_back=7): 
        """Comprehensive scraping for a specific policy"""
        print(f"Scraping data for: {policy_name}")
        
        all_data = []
        
        policy_queries = {
            'Digital India': ['digital india', 'digitalization india', 'e-governance'],
            'Swachh Bharat': ['swachh bharat', 'clean india', 'swachh mission'],
            'Make in India': ['make in india', 'atmanirbhar bharat', 'manufacturing india'],
            'Jan Dhan Yojana': ['jan dhan yojana', 'financial inclusion india'],
            'Ayushman Bharat': ['ayushman bharat', 'healthcare india', 'pmjay']
        }
        
        queries = policy_queries.get(policy_name, [policy_name.lower()])
        
        for query in queries:
            print(f"Searching for: {query}")
            
            # --- Twitter data (COMMENTED OUT FOR POC) ---
            # if self.twitter_api:
            #     # Add a mandatory sleep *before* each Twitter query
            #     time.sleep(15) 
            #     twitter_data = self.scrape_twitter_data(query, max_tweets=10) 
            #     if not twitter_data.empty:
            #         all_data.append(twitter_data)
            #         print(f"Found {len(twitter_data)} tweets")
            
            # Reddit data
            reddit_data = self.scrape_reddit_data('india', query, limit=20) 
            if not reddit_data.empty:
                all_data.append(reddit_data)
                print(f"Found {len(reddit_data)} Reddit posts")
            
            # Add a general delay between queries across different platforms too
            time.sleep(5) 
        
        if all_data:
            combined_data = pd.concat(all_data, ignore_index=True)
            
            # --- Timezone Handling for Comparison ---
            utc_now = datetime.now(pytz.utc)
            cutoff_date = utc_now - timedelta(days=days_back)
            
            def make_utc_aware_series(dt_series):
                dt_series = pd.to_datetime(dt_series, errors='coerce') 
                if dt_series.dt.tz is None: 
                    return dt_series.dt.tz_localize(pytz.utc)
                else: 
                    return dt_series.dt.tz_convert(pytz.utc)

            combined_data['date'] = make_utc_aware_series(combined_data['date'])
            
            combined_data = combined_data[combined_data['date'] >= cutoff_date]
            
            combined_data = combined_data.drop_duplicates(subset=['text'])
            
            return combined_data
        
        return pd.DataFrame()

def main():
    """Example usage of the scraper"""
    scraper = SocialMediaScraper()
    
    data = scraper.scrape_policy_data('Digital India', days_back=7) 
    
    if not data.empty:
        print(f"Scraped {len(data)} posts")
        print(data.head())
        
        # Save to CSV
        filename = f"scraped_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        data.to_csv(filename, index=False)
        print(f"Data saved to {filename}")
    else:
        print("No data scraped. Check API keys, network connection, or if rate limits are hit too frequently.")
        print("Consider running the dashboard in 'Demo Mode' with sample data for a quick POC demonstration.")

if __name__ == "__main__":
    main()