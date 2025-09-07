# bot.py (v5 - The Ultimate Photos API Bot)

import os
import json
import requests
from bs4 import BeautifulSoup
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import time
from urllib.parse import urljoin
import re

# --- Configuration ---
BLOG_ID = os.getenv('BLOG_ID')
CONFIG_FILE = 'config.json'
STATE_FILE = 'posted_chapters.json'
# --- নতুন: Photos API-এর জন্য স্কোপ যোগ করা ---
SCOPES = ['https://www.googleapis.com/auth/blogger', 'https://www.googleapis.com/auth/photoslibrary.appendonly']
G_CLIENT_ID = os.getenv('G_CLIENT_ID')
G_CLIENT_SECRET = os.getenv('G_CLIENT_SECRET')
G_REFRESH_TOKEN = os.getenv('G_REFRESH_TOKEN')

# --- Helper Functions ---
def load_json(file_path, default_data):
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            try: return json.load(f)
            except json.JSONDecodeError: return default_data
    return default_data

def save_json(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_google_service(service_name, version, creds):
    """যেকোনো Google সার্ভিস তৈরি করার জন্য একটি সাধারণ ফাংশন"""
    try:
        return build(service_name, version, credentials=creds)
    except Exception as e:
        print(f"Error creating {service_name} service: {e}")
        return None

# --- নতুন এবং উন্নত আপলোড ফাংশন ---
def upload_image_and_get_url(photos_service, image_url, referer):
    """ছবি ডাউনলোড করে Google Photos-এ আপলোড করে এবং শেয়ারযোগ্য লিঙ্ক তৈরি করে"""
    try:
        print(f"    Downloading image: {image_url}")
        image_response = requests.get(image_url, headers={'User-Agent': 'Mozilla/5.0', 'Referer': referer}, timeout=60)
        image_response.raise_for_status()
        image_bytes = image_response.content
        
        # ধাপ ১: Google Photos-এ ছবিটি আপলোড করা
        print("    Uploading to Google Photos...")
        upload_response = photos_service.uploads().upload(body=image_bytes).execute()
        upload_token = upload_response
        
        if not upload_token:
            print("    Upload failed, did not receive upload token.")
            return None
        
        # ধাপ ২: আপলোড টোকেন ব্যবহার করে মিডিয়া আইটেম তৈরি করা
        print("    Creating media item in Google Photos...")
        new_media_item = {
            'newMediaItems': [{
                "simpleMediaItem": {"uploadToken": upload_token}
            }]
        }
        media_creation_response = photos_service.mediaItems().batchCreate(body=new_media_item).execute()
        
        # Google Photos থেকে পাওয়া ছবির লিঙ্কটি সরাসরি ব্যবহার করা যায় না, আমাদের একটি বিশেষ ফরম্যাট ব্যবহার করতে হবে
        # এই লিঙ্কটি ছবির সর্বোচ্চ কোয়ালিটি দেখাবে
        base_url = media_creation_response['newMediaItemResults'][0]['mediaItem']['baseUrl']
        final_url = f"{base_url}=w1600-h0" # 's0' এর Photos সংস্করণ
        
        return final_url
            
    except Exception as e:
        print(f"    An error occurred during image upload: {e}")
        return None

# --- Main Post and Chapter Post Logic (আগের মতোই, শুধু আপলোড ফাংশন পরিবর্তন হবে) ---
# ... (এখানে থাকা বাকি ফাংশনগুলো আগের মতোই থাকবে, তাই আমি সেগুলো আবার না দিয়ে শুধু main() ফাংশনটি দিচ্ছি) ...

def get_jikan_manga_details(series_name):
    # ... আগের মতোই ...
    print(f"  Fetching details for '{series_name}' from Jikan API...")
    try:
        search_url = f"https://api.jikan.moe/v4/manga?q={series_name.replace(' ', '%20')}&limit=1"
        response = requests.get(search_url, timeout=30)
        response.raise_for_status()
        results = response.json().get('data', [])
        if not results: return None
        return results[0]
    except requests.RequestException as e:
        print(f"  Error fetching Jikan data: {e}"); return None

def create_main_post(blogger_service, photos_service, series_name):
    # ... আগের মতোই ...
    print(f"  Main post for '{series_name}' does not exist. Creating it now...")
    details = get_jikan_manga_details(series_name)
    if not details: return False

    title = details.get('title', series_name)
    synopsis = details.get('synopsis', 'No synopsis available.')
    cover_url_original = details.get('images', {}).get('jpg', {}).get('large_image_url', '')
    if not cover_url_original: return False
        
    print("  Uploading cover image...")
    cover_url_final = upload_image_and_get_url(photos_service, cover_url_original, 'https://myanimelist.net/')
    if not cover_url_final:
        print("  Failed to upload cover image. Skipping main post creation.")
        return False
        
    labels = [tag.get('name') for tag in details.get('genres', [])]
    labels.append("Series"); labels.append(series_name)
    
    cover_html = f'<div class="separator" style="text-align: center;"><img src="{cover_url_final}" /></div>'
    content = f'{cover_html}<p>{synopsis}</p><!--chapter-list--><div class="chapter_get" data-labelchapter="{series_name}"></div>'
    
    try:
        body = {"title": title, "content": content, "labels": list(set(labels))}
        post = blogger_service.posts().insert(blogId=BLOG_ID, body=body, isDraft=False).execute()
        print(f"  Successfully created main post: '{post['title']}'")
        return True
    except Exception as e:
        print(f"  Error creating main post on Blogger: {e}"); return False

def scrape_chapters(series_config):
    # ... আগের মতোই ...
    list_url, selectors = series_config['list_url'], series_config['selectors']
    print(f"  Scraping chapter list from {list_url}")
    try:
        response = requests.get(list_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        all_chapters = []
        chapter_items = soup.select(selectors['chapter_list_item'])
        for item in chapter_items:
            link_tag = item.select_one(selectors['chapter_link'])
            title_tag = item.select_one(selectors['chapter_title'])
            if not link_tag or not title_tag: continue
            chapter_url = link_tag.get('href', '').strip()
            if chapter_url and not chapter_url.startswith('http'):
                chapter_url = urljoin(list_url, chapter_url)
            if chapter_url:
                all_chapters.append({'title': title_tag.text.strip(), 'url': chapter_url})
        return list(reversed(all_chapters))
    except requests.RequestException as e:
        print(f"  Error scraping chapter list: {e}"); return []

def create_chapter_post(blogger_service, photos_service, series_name, chapter_info, image_selector):
    # ... আগের মতোই ...
    chapter_title, chapter_url = chapter_info['title'], chapter_info['url']
    print(f"\n- Processing Chapter: {chapter_title}")
    try:
        response = requests.get(chapter_url, headers={'User-agent': 'Mozilla/5.0'}, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        image_tags = soup.select(image_selector)
        if not image_tags: return False, None
        
        html_content = ""
        for i, img_tag in enumerate(image_tags):
            img_url = img_tag.get('data-src', img_tag.get('src', '')).strip()
            if not img_url: continue
            
            print(f"  Processing image {i+1}/{len(image_tags)}")
            final_img_url = upload_image_and_get_url(photos_service, img_url, chapter_url)
            if final_img_url:
                html_content += f'<div class="separator" style="text-align: center;"><img src="{final_img_url}" /></div>\n'
            else:
                print("    Image upload failed.")
            time.sleep(5)
        
        if not html_content: return False, None

        body = {"title": chapter_title, "content": html_content, "labels": ["Chapter", series_name]}
        post = blogger_service.posts().insert(blogId=BLOG_ID, body=body, isDraft=False).execute()
        print(f"  Successfully posted: '{post['title']}'")
        return True, chapter_url
    except Exception as e:
        print(f"  An error occurred while creating chapter post: {e}"); return False, None

# --- Main Bot Logic (চূড়ান্ত সংস্করণ) ---
def main():
    configs = load_json(CONFIG_FILE, [])
    state = load_json(STATE_FILE, {"main_posts_created": [], "chapters_posted": {}})
    
    if not configs:
        print("Config file is empty. Exiting."); return
    
    # ক্রেডেনশিয়াল তৈরি
    creds_info = {
        "client_id": G_CLIENT_ID, "client_secret": G_CLIENT_SECRET,
        "refresh_token": G_REFRESH_TOKEN, "token_uri": "https://oauth2.googleapis.com/token",
    }
    creds = Credentials.from_authorized_user_info(info=creds_info, scopes=SCOPES)
    
    # দুটি সার্ভিসই তৈরি করা হচ্ছে
    blogger_service = get_google_service('blogger', 'v3', creds)
    photos_service = get_google_service('photoslibrary', 'v1', creds)

    if not blogger_service or not photos_service:
        print("Could not connect to Google services. Exiting."); return

    for config in configs:
        series_name = config['name']
        print(f"\n--- Processing Series: {series_name} ---")
        
        if series_name not in state["main_posts_created"]:
            success = create_main_post(blogger_service, photos_service, series_name)
            if success:
                state["main_posts_created"].append(series_name)
                save_json(STATE_FILE, state)
                time.sleep(60)
            else:
                time.sleep(120); continue

        all_chapters_on_site = scrape_chapters(config)
        if series_name not in state["chapters_posted"]:
            state["chapters_posted"][series_name] = []
        
        posted_chapter_urls = state["chapters_posted"][series_name]
        chapters_to_post = [ch for ch in all_chapters_on_site if ch['url'] not in posted_chapter_urls]
        
        if not chapters_to_post:
            print(f"  No new chapters to post for {series_name}.")
            time.sleep(120); continue
        
        for chapter in chapters_to_post:
            success, posted_url = create_chapter_post(blogger_service, photos_service, series_name, chapter, config['selectors']['chapter_image'])
            if success and posted_url:
                state["chapters_posted"][series_name].append(posted_url)
                save_json(STATE_FILE, state)
            time.sleep(30)
        time.sleep(120)

    print("\n--- All series processed. Bot finished. ---")


if __name__ == '__main__':
    if not all([BLOG_ID, G_CLIENT_ID, G_CLIENT_SECRET, G_REFRESH_TOKEN]):
        print("Error: Required Google API secrets are missing.")
    else:
        main()
