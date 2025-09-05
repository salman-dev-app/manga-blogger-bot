# bot.py (v2 - Multi-Series Support)

import os
import json
import requests
from bs4 import BeautifulSoup
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import base64
import time
from urllib.parse import urljoin

# --- Configuration ---
# এই ভ্যারিয়েবলগুলোর মান এখন GitHub Secrets থেকে আসবে
IMGBB_API_KEY = os.getenv('IMGBB_API_KEY')
BLOG_ID = os.getenv('BLOG_ID')

# লোকাল ফাইলের নাম
CONFIG_FILE = 'config.json'
STATE_FILE = 'posted_chapters.json'

# --- Google API Configuration ---
SCOPES = ['https://www.googleapis.com/auth/blogger']
G_CLIENT_ID = os.getenv('G_CLIENT_ID')
G_CLIENT_SECRET = os.getenv('G_CLIENT_SECRET')
G_REFRESH_TOKEN = os.getenv('G_REFRESH_TOKEN')

def load_config():
    """config.json থেকে সিরিজের তালিকা লোড করে"""
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: {CONFIG_FILE} not found! Please create it.")
        return []
    except json.JSONDecodeError:
        print(f"Error: Could not decode {CONFIG_FILE}. Please check its format.")
        return []

def get_posted_data():
    """posted_chapters.json থেকে সব সিরিজের পোস্ট করা চ্যাপ্টারের তালিকা লোড করে"""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"Warning: Could not decode {STATE_FILE}. Starting fresh.")
            return {}
    return {}

def save_posted_data(posted_data):
    """পোস্ট করার পর সম্পূর্ণ ডেটা সেভ করে"""
    with open(STATE_FILE, 'w') as f:
        json.dump(posted_data, f, indent=2)

def scrape_website_for_new_chapters(series_config, posted_chapters_for_series):
    """একটি নির্দিষ্ট সিরিজের জন্য নতুন চ্যাপ্টার খুঁজে বের করে"""
    list_url = series_config['list_url']
    selectors = series_config['selectors']
    print(f"Scraping '{series_config['name']}' from {list_url}")
    
    try:
        response = requests.get(list_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        new_chapters = []
        chapter_list_items = soup.select(selectors['chapter_list_item'])
        
        if not chapter_list_items:
            print(f"Warning: No chapter list items found for '{series_config['name']}' with selector '{selectors['chapter_list_item']}'.")
            return []

        for item in chapter_list_items:
            link_tag = item.select_one(selectors['chapter_link'])
            title_tag = item.select_one(selectors['chapter_title'])
            
            if not link_tag or not title_tag:
                continue

            chapter_url = link_tag.get('href', '').strip()
            # কিছু সাইট 상대 (relative) URL ব্যবহার করে, তাই সম্পূর্ণ URL তৈরি করতে হবে
            if chapter_url and not chapter_url.startswith('http'):
                chapter_url = urljoin(list_url, chapter_url)

            chapter_title = title_tag.text.strip()
            
            if chapter_url and chapter_url not in posted_chapters_for_series:
                new_chapters.append({'title': chapter_title, 'url': chapter_url})
            
        print(f"Found {len(new_chapters)} new chapters for '{series_config['name']}'.")
        return list(reversed(new_chapters))
        
    except requests.RequestException as e:
        print(f"Error scraping list page for '{series_config['name']}': {e}")
        return []

def get_image_urls_from_chapter(chapter_url, image_selector):
    """চ্যাপ্টারের পেজ থেকে ছবির URL বের করে"""
    print(f"Getting images from: {chapter_url}")
    try:
        response = requests.get(chapter_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        image_urls = []
        image_tags = soup.select(image_selector)
        
        if not image_tags:
            print(f"Warning: No images found on chapter page with selector '{image_selector}'.")
            return []

        for img_tag in image_tags:
            # অনেক সাইট lazy loading ব্যবহার করে, তাই 'data-src' বা অন্য attribute চেক করতে হতে পারে
            img_url = img_tag.get('data-src', img_tag.get('src', '')).strip()
            if img_url:
                image_urls.append(img_url)
        print(f"Found {len(image_urls)} images.")
        return image_urls
    except requests.RequestException as e:
        print(f"Error getting images from chapter: {e}")
        return []

def upload_image_to_imgbb(image_url):
    """ImgBB-তে ছবি আপলোড করে"""
    try:
        # কিছু সাইট সরাসরি ডাউনলোড ব্লক করে, তাই User-Agent এবং Referer হেডার জরুরি
        response = requests.get(image_url, headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'https://google.com'}, timeout=60)
        response.raise_for_status()
        
        image_b64 = base64.b64encode(response.content)
        
        payload = {"key": IMGBB_API_KEY, "image": image_b64}
        upload_response = requests.post("https://api.imgbb.com/1/upload", data=payload, timeout=60)
        upload_response.raise_for_status()
        
        result = upload_response.json()
        if result.get('data', {}).get('url'):
            return result['data']['url']
        else:
            print(f"ImgBB upload failed: {result.get('error', {}).get('message', 'Unknown error')}")
            return None
    except requests.RequestException as e:
        print(f"Error uploading image {image_url}: {e}")
        return None

def get_blogger_service():
    """Google API-এর সাথে সংযোগ স্থাপন করে"""
    try:
        creds_info = {
            "client_id": G_CLIENT_ID,
            "client_secret": G_CLIENT_SECRET,
            "refresh_token": G_REFRESH_TOKEN,
            "token_uri": "https://oauth2.googleapis.com/token",
        }
        creds = Credentials.from_authorized_user_info(info=creds_info, scopes=SCOPES)
        # টোকেন ভ্যালিড কিনা বা এক্সপায়ার্ড কিনা তা চেক করার প্রয়োজন নেই,
        # লাইব্রেরি নিজে থেকেই রিফ্রেশ করে নেবে যখন দরকার হবে।
        return build('blogger', 'v3', credentials=creds)
    except Exception as e:
        print(f"Error creating Blogger service: {e}")
        return None

def create_blogger_post(service, title, content, labels):
    """Blogger-এ পোস্ট তৈরি করে"""
    try:
        body = {"title": title, "content": content, "labels": labels}
        post = service.posts().insert(blogId=BLOG_ID, body=body, isDraft=False).execute()
        print(f"Successfully posted: '{post['title']}'")
        return True
    except Exception as e:
        print(f"Error posting to Blogger: {e}")
        return False

def main():
    """বটের মূল চালিকাশক্তি"""
    all_series_config = load_config()
    if not all_series_config:
        print("Bot exiting because config file is empty or missing.")
        return

    posted_data = get_posted_data()
    blogger_service = get_blogger_service()

    if not blogger_service:
        print("Bot exiting due to Blogger service initialization failure.")
        return

    for series_config in all_series_config:
        series_name = series_config.get('name', 'Unnamed Series')
        print(f"\n--- Processing Series: {series_name} ---")
        
        posted_chapters_for_this_series = posted_data.get(series_name, [])
        new_chapters = scrape_website_for_new_chapters(series_config, posted_chapters_for_this_series)
        
        if not new_chapters:
            print(f"No new chapters to post for {series_name}.")
            continue

        for chapter in new_chapters:
            chapter_title, chapter_url = chapter['title'], chapter['url']
            print(f"\n- Processing Chapter: {chapter_title}")
            
            image_urls = get_image_urls_from_chapter(chapter_url, series_config['selectors']['chapter_image'])
            if not image_urls:
                print(f"Could not get images for {chapter_title}. Skipping."); continue

            uploaded_image_links = []
            for i, img_url in enumerate(image_urls):
                print(f"  Uploading image {i+1}/{len(image_urls)}...")
                new_link = upload_image_to_imgbb(img_url)
                if new_link:
                    uploaded_image_links.append(new_link)
                else:
                    print("  Skipping this chapter due to an image upload failure.")
                    break
                time.sleep(1) # ImgBB API-কে সময় দেওয়ার জন্য ১ সেকেন্ড বিরতি

            if len(uploaded_image_links) != len(image_urls):
                continue

            html_content = "".join([f'<div class="separator" style="text-align: center;"><img src="{link}" /></div>' for link in uploaded_image_links])
            labels = ["Chapter", series_name]
            
            if create_blogger_post(blogger_service, chapter_title, html_content, labels):
                if series_name not in posted_data:
                    posted_data[series_name] = []
                posted_data[series_name].append(chapter_url)
                save_posted_data(posted_data)
                print("  State file updated.")
            
            print("  Waiting for 10 seconds before processing the next chapter...")
            time.sleep(10) # দুটি পোস্টের মধ্যে কিছুটা বিরতি

        print(f"Finished processing series: {series_name}")
        print("Waiting for 30 seconds before starting the next series...")
        time.sleep(30) # দুটি সিরিজের মধ্যে কিছুটা বিরতি

    print("\n--- All series processed. Bot finished. ---")


if __name__ == '__main__':
    # নিশ্চিত করুন যে প্রয়োজনীয় API Key গুলো সেট করা আছে
    if not all([IMGBB_API_KEY, BLOG_ID, G_CLIENT_ID, G_CLIENT_SECRET, G_REFRESH_TOKEN]):
        print("Error: One or more required environment variables (API Keys/Secrets) are missing.")
        print("Please check your GitHub repository's Secrets configuration.")
    else:
        main()
