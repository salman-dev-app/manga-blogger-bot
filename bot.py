# bot.py (v5.1 - The Patient & Reliable Blogger Uploader+)

import os
import json
import requests
from bs4 import BeautifulSoup
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import time
from urllib.parse import urljoin
import re
import base64

# --- Configuration & Helper Functions ---
BLOG_ID = os.getenv('BLOG_ID')
CONFIG_FILE = 'config.json'
STATE_FILE = 'posted_chapters.json'
SCOPES = ['https://www.googleapis.com/auth/blogger']
G_CLIENT_ID = os.getenv('G_CLIENT_ID')
G_CLIENT_SECRET = os.getenv('G_CLIENT_SECRET')
G_REFRESH_TOKEN = os.getenv('G_REFRESH_TOKEN')

def load_json(file_path, default_data):
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            try: return json.load(f)
            except json.JSONDecodeError: return default_data
    return default_data

def save_json(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_blogger_service():
    try:
        creds_info = {"client_id": G_CLIENT_ID, "client_secret": G_CLIENT_SECRET, "refresh_token": G_REFRESH_TOKEN, "token_uri": "https://oauth2.googleapis.com/token"}
        creds = Credentials.from_authorized_user_info(info=creds_info, scopes=SCOPES)
        return build('blogger', 'v3', credentials=creds)
    except Exception as e:
        print(f"Error creating Blogger service: {e}"); return None

# --- নতুন এবং উন্নত আপলোড ফাংশন ---
def upload_image_to_blogger(service, image_url, referer):
    """ছবি ডাউনলোড করে একটি ড্রাফট পোস্টে আপলোড করে এবং Blogger-এর নিজস্ব লিঙ্ক বের করে আনে"""
    try:
        print(f"    Downloading image: {image_url}")
        image_response = requests.get(image_url, headers={'User-Agent': 'Mozilla/5.0', 'Referer': referer}, timeout=60)
        image_response.raise_for_status()
        
        image_b64 = base64.b64encode(image_response.content).decode('utf-8')
        content_type = image_response.headers.get('content-type', 'image/jpeg')
        
        draft_title = f"temp_image_upload_{int(time.time())}"
        draft_content = f'<img src="data:{content_type};base64,{image_b64}" />'
        draft_body = {"title": draft_title, "content": draft_content}
        
        print("    Uploading to a temporary draft post...")
        draft_post = service.posts().insert(blogId=BLOG_ID, body=draft_body, isDraft=True).execute()
        draft_post_id = draft_post['id']
        
        # --- মূল পরিবর্তন: Blogger-কে ছবিটি প্রসেস করার জন্য ৩০ সেকেন্ড সময় দেওয়া ---
        print("    Waiting 30 seconds for Blogger to process the image...")
        time.sleep(30) # ৩০ সেকেন্ড অপেক্ষা
        
        retrieved_post = service.posts().get(blogId=BLOG_ID, postId=draft_post_id).execute()
        post_content = retrieved_post.get('content', '')
        match = re.search(r'src="(https://blogger\.googleusercontent\.com/[^"]+)"', post_content)
        
        service.posts().delete(blogId=BLOG_ID, postId=draft_post_id).execute()
        print("    Temporary draft post deleted.")

        if match:
            blogger_url = match.group(1)
            return re.sub(r'\/s\d+([-\w]*)\/', '/s0/', blogger_url)
        else:
            print("    Could not extract Blogger URL. Base64 might still be present.")
            return None
            
    except Exception as e:
        print(f"    An error occurred during image upload: {e}")
        return None

# --- Main Post and Chapter Post Logic (অপরিবর্তিত) ---
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

def create_main_post(service, series_name):
    # ... আগের মতোই ...
    print(f"  Main post for '{series_name}' does not exist. Creating it now...")
    details = get_jikan_manga_details(series_name)
    if not details: return False
    title = details.get('title', series_name)
    synopsis = details.get('synopsis', 'No synopsis available.')
    cover_url_original = details.get('images', {}).get('jpg', {}).get('large_image_url', '')
    if not cover_url_original: return False
    print("  Uploading cover image...")
    cover_url_blogger = upload_image_to_blogger(service, cover_url_original, 'https://myanimelist.net/')
    if not cover_url_blogger:
        print("  Failed to upload cover image. Skipping main post creation.")
        return False
    labels = [tag.get('name') for tag in details.get('genres', [])]
    labels.append("Series"); labels.append(series_name)
    cover_html = f'<div class="separator" style="text-align: center;"><img src="{cover_url_blogger}" /></div>'
    content = f'{cover_html}<p>{synopsis}</p><!--chapter-list--><div class="chapter_get" data-labelchapter="{series_name}"></div>'
    try:
        body = {"title": title, "content": content, "labels": list(set(labels))}
        post = service.posts().insert(blogId=BLOG_ID, body=body, isDraft=False).execute()
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

def create_chapter_post(service, series_name, chapter_info, image_selector):
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
            blogger_img_url = upload_image_to_blogger(service, img_url, chapter_url)
            if blogger_img_url:
                html_content += f'<div class="separator" style="text-align: center;"><img src="{blogger_img_url}" /></div>\n'
            else:
                print("    Image upload failed. Skipping this image.")
            time.sleep(5)
        
        if not html_content: return False, None

        body = {"title": chapter_title, "content": html_content, "labels": ["Chapter", series_name]}
        post = service.posts().insert(blogId=BLOG_ID, body=body, isDraft=False).execute()
        print(f"  Successfully posted: '{post['title']}'")
        return True, chapter_url
    except Exception as e:
        print(f"  An error occurred while creating chapter post: {e}"); return False, None

def main():
    # ... (এই ফাংশনটি আগের মতোই থাকবে) ...
    configs = load_json(CONFIG_FILE, [])
    state = load_json(STATE_FILE, {"main_posts_created": [], "chapters_posted": {}})
    if not configs: print("Config file is empty. Exiting."); return
    blogger_service = get_blogger_service()
    if not blogger_service: print("Could not connect to Blogger. Exiting."); return

    for config in configs:
        series_name = config['name']
        print(f"\n--- Processing Series: {series_name} ---")
        if series_name not in state["main_posts_created"]:
            success = create_main_post(blogger_service, series_name)
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
            success, posted_url = create_chapter_post(blogger_service, series_name, chapter, config['selectors']['chapter_image'])
            if success and posted_url:
                state["chapters_posted"][series_name].append(posted_url)
                save_json(STATE_FILE, state)
            time.sleep(30)
        time.sleep(120)

    print("\n--- All series processed. Bot finished. ---")

if __name__ == '__main__':
    main()
