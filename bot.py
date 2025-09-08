# bot.py (v8.1 - The Ultimate Simple & Reliable ImgBB Bot - Final Version)

import os
import json
import requests
from bs4 import BeautifulSoup
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import time
from urllib.parse import urljoin
import base64

# --- Configuration & Helper Functions ---
BLOG_ID = os.getenv('BLOG_ID')
IMGBB_API_KEY = os.getenv('IMGBB_API_KEY')
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

def upload_image_to_imgbb(image_url, referer):
    """সরাসরি API ব্যবহার করে ImgBB-তে ছবি আপলোড করে"""
    try:
        print(f"    Downloading image: {image_url}")
        image_response = requests.get(image_url, headers={'User-Agent': 'Mozilla/5.0', 'Referer': referer}, timeout=60)
        image_response.raise_for_status()
        
        image_b64 = base64.b64encode(image_response.content)
        
        upload_url = "https://api.imgbb.com/1/upload"
        payload = { "key": IMGBB_API_KEY, "image": image_b64 }
        
        print("    Uploading to ImgBB via API...")
        upload_response = requests.post(upload_url, data=payload, timeout=120)
        upload_response.raise_for_status()
        
        result = upload_response.json()
        if result.get('data') and result['data'].get('url'):
            print(f"    ImgBB upload successful: {result['data']['url']}")
            return result['data']['url']
        else:
            print(f"    ImgBB upload failed: {result}")
            return None
    except requests.RequestException as e:
        print(f"    Error during ImgBB upload: {e}")
        return None

def get_jikan_manga_details(series_name):
    print(f"    Fetching details for '{series_name}' from Jikan API...")
    try:
        search_url = f"https://api.jikan.moe/v4/manga?q={series_name.replace(' ', '%20')}&limit=1"
        response = requests.get(search_url, timeout=30)
        response.raise_for_status()
        results = response.json().get('data', [])
        if not results:
            print(f"    Could not find '{series_name}' on MyAnimeList.")
            return None
        return results[0]
    except requests.RequestException as e:
        print(f"    Error fetching Jikan data: {e}"); return None

def create_main_post(service, series_name):
    print(f"  Creating main post for '{series_name}'...")
    details = get_jikan_manga_details(series_name)
    if not details: return False
    
    title = details.get('title', series_name)
    synopsis = details.get('synopsis', 'No synopsis available.')
    cover_url_original = details.get('images', {}).get('jpg', {}).get('large_image_url', '')
    if not cover_url_original: return False
        
    print("    Uploading cover image via ImgBB...")
    cover_url_final = upload_image_to_imgbb(cover_url_original, 'https://myanimelist.net/')
    if not cover_url_final:
        print("    Failed to upload cover image. Skipping main post creation.")
        return False
        
    labels = [tag.get('name') for tag in details.get('genres', [])]
    labels.append("Series"); labels.append(series_name)
    cover_html = f'<div class="separator" style="text-align: center;"><img src="{cover_url_final}" /></div>'
    content = f'{cover_html}<p>{synopsis}</p><!--chapter-list--><div class="chapter_get" data-labelchapter="{series_name}"></div>'
    
    try:
        body = {"title": title, "content": content, "labels": list(set(labels))}
        post = service.posts().insert(blogId=BLOG_ID, body=body, isDraft=False).execute()
        print(f"    Successfully created main post: '{post['title']}'")
        return True
    except Exception as e:
        print(f"    Error creating main post on Blogger: {e}"); return False

def scrape_chapters(series_config):
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
            imgbb_url = upload_image_to_imgbb(img_url, chapter_url)
            
            if imgbb_url:
                html_content += f'<div class="separator" style="text-align: center;"><img src="{imgbb_url}" /></div>\n'
            else:
                print("    Image upload failed. Skipping this image.")
            
            # --- পরিবর্তন: নিরাপদ বিরতির জন্য ১৫ সেকেন্ড ---
            time.sleep(15)
        
        if not html_content: return False, None

        body = {"title": chapter_title, "content": html_content, "labels": ["Chapter", series_name]}
        post = service.posts().insert(blogId=BLOG_ID, body=body, isDraft=False).execute()
        print(f"  Successfully posted: '{post['title']}'")
        return True, chapter_url
    except Exception as e:
        print(f"  An error occurred: {e}"); return False, None

def main():
    configs = load_json(CONFIG_FILE, [])
    state = load_json(STATE_FILE, {"main_posts_created": [], "chapters_posted": {}})
    blogger_service = get_blogger_service()

    if not blogger_service:
        print("Could not initialize Blogger service. Exiting.")
        return

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

if __name__ == '__main__':
    if not all([BLOG_ID, G_CLIENT_ID, G_CLIENT_SECRET, G_REFRESH_TOKEN, IMGBB_API_KEY]):
        print("Error: One or more required secrets are missing.")
    else:
        main()
