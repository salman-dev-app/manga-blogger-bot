# bot.py (v10.2 - The Ultimate Smart & Resourceful Bot)

import os
import json
import requests
from bs4 import BeautifulSoup
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import time
from urllib.parse import urljoin
import schedule
import cloudinary
import cloudinary.uploader
from config import BLOG_ID, G_CLIENT_ID, G_CLIENT_SECRET, G_REFRESH_TOKEN, CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET, CONFIG_FILE, SCOPES
from database import get_state, save_state

# --- Cloudinary Configuration ---
cloudinary.config(
  cloud_name = CLOUDINARY_CLOUD_NAME, 
  api_key = CLOUDINARY_API_KEY, 
  api_secret = CLOUDINARY_API_SECRET,
  secure = True
)

# --- Helper Functions ---
def get_blogger_service():
    try:
        creds_info = {"client_id": G_CLIENT_ID, "client_secret": G_CLIENT_SECRET, "refresh_token": G_REFRESH_TOKEN, "token_uri": "https://oauth2.googleapis.com/token"}
        creds = Credentials.from_authorized_user_info(info=creds_info, scopes=SCOPES)
        return build('blogger', 'v3', credentials=creds)
    except Exception as e:
        print(f"Error creating Blogger service: {e}"); return None

def upload_image_to_cloudinary(image_url, referer):
    try:
        print(f"    - Downloading image: {image_url}")
        image_response = requests.get(image_url, headers={'User-Agent': 'Mozilla/5.0', 'Referer': referer}, timeout=60)
        image_response.raise_for_status()
        
        print(f"    - Uploading downloaded image to Cloudinary...")
        upload_result = cloudinary.uploader.upload(image_response.content, fetch_format="auto", quality="auto:good")
        
        secure_url = upload_result.get('secure_url')
        if secure_url:
            print(f"    - Cloudinary upload successful: {secure_url}")
            return secure_url
        else:
            print(f"    - Cloudinary upload failed: {upload_result.get('error', 'Unknown error')}")
            return None
    except Exception as e:
        print(f"    - Error during Cloudinary upload: {e}")
        return None

def get_jikan_manga_details(series_name):
    print(f"  - Fetching details for '{series_name}' from Jikan API...")
    try:
        search_url = f"https://api.jikan.moe/v4/manga?q={series_name.replace(' ', '%20')}&limit=1"
        response = requests.get(search_url, timeout=30)
        response.raise_for_status()
        results = response.json().get('data', [])
        if not results: return None
        return results[0]
    except requests.RequestException as e:
        print(f"    - Error fetching Jikan data: {e}"); return None

def create_main_post(service, series_name):
    print(f"  - Creating main post for '{series_name}'...")
    details = get_jikan_manga_details(series_name)
    if not details: return False
    
    title = details.get('title', series_name)
    synopsis = details.get('synopsis', 'No synopsis available.')
    cover_url_original = details.get('images', {}).get('jpg', {}).get('large_image_url', '')
    if not cover_url_original: return False
        
    print("    - Uploading cover image...")
    cover_url_final = upload_image_to_cloudinary(cover_url_original, 'https://myanimelist.net/')
    if not cover_url_final:
        print("    - Failed to upload cover image. Skipping.")
        return False
        
    labels = [tag.get('name') for tag in details.get('genres', [])]
    labels.append("Series"); labels.append(series_name)
    cover_html = f'<div class="separator" style="text-align: center;"><img src="{cover_url_final}" /></div>'
    content = f'{cover_html}<p>{synopsis}</p><!--chapter-list--><div class="chapter_get" data-labelchapter="{series_name}"></div>'
    
    try:
        body = {"title": title, "content": content, "labels": list(set(labels))}
        post = service.posts().insert(blogId=BLOG_ID, body=body, isDraft=False).execute()
        print(f"    - Successfully created main post: '{post['title']}'")
        return True
    except HttpError as e:
        if e.resp.status == 403:
            print("    - Blogger API quota reached. Cannot create main post.")
        else:
            print(f"    - Error creating main post on Blogger: {e}")
        return False
    except Exception as e:
        print(f"    - Unexpected error creating main post: {e}"); return False

def scrape_chapters(series_config):
    list_url, selectors = series_config['list_url'], series_config['selectors']
    print(f"  - Scraping chapter list from {list_url}")
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
        print(f"  - Error scraping chapter list: {e}"); return []

def create_chapter_post(service, series_name, chapter_info, image_selector):
    chapter_title, chapter_url = chapter_info['title'], chapter_info['url']
    print(f"\n- Processing Chapter: {chapter_title}")
    
    # --- নতুন: ছবি আপলোড করার আগে, একটি ডামি পোস্ট করার চেষ্টা করে কোটা চেক করা ---
    try:
        print("  - Checking Blogger API quota before uploading images...")
        service.posts().insert(blogId=BLOG_ID, body={"title": "Quota Check"}, isDraft=True).execute()
        print("  - Quota check successful. Proceeding with image uploads.")
    except HttpError as e:
        if e.resp.status == 403:
            print("  - Blogger API quota reached. Halting all uploads for this series.")
            return "QUOTA_EXCEEDED", None
        else:
            print(f"  - An unexpected API error occurred during quota check: {e}")
            return False, None
    except Exception as e:
        print(f"  - A general error occurred during quota check: {e}")
        return False, None

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
            
            print(f"  - Processing image {i+1}/{len(image_tags)}")
            cloudinary_url = upload_image_to_cloudinary(img_url, chapter_url)
            
            if cloudinary_url:
                html_content += f'<div class="separator" style="text-align: center;"><img src="{cloudinary_url}" /></div>\n'
            else:
                print("    - Image upload failed. Skipping this image.")
            time.sleep(2)
        
        if not html_content: return False, None

        body = {"title": chapter_title, "content": html_content, "labels": ["Chapter", series_name]}
        post = service.posts().insert(blogId=BLOG_ID, body=body, isDraft=False).execute()
        print(f"  - Successfully posted: '{post['title']}'")
        return True, chapter_url
    except HttpError as e:
        if e.resp.status == 403:
            print("  - Blogger API quota reached during final post creation.")
            return "QUOTA_EXCEEDED", None
        else:
            print(f"  - An API error occurred while creating chapter post: {e}")
            return False, None
    except Exception as e:
        print(f"  - A general error occurred while creating chapter post: {e}"); return False, None

def job():
    print(f"\n--- Running scheduled job at {time.ctime()} ---")
    
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        configs = json.load(f)

    state = get_state()
    blogger_service = get_blogger_service()
    if not blogger_service: return

    for config in configs:
        series_name = config['name']
        print(f"\n--- Processing Series: {series_name} ---")
        
        if series_name not in state["main_posts_created"]:
            if create_main_post(blogger_service, series_name):
                state["main_posts_created"].append(series_name)
                save_state(state)
                time.sleep(60)
            else:
                time.sleep(120); continue
        
        all_chapters_on_site = scrape_chapters(config)
        if series_name not in state["chapters_posted"]:
            state["chapters_posted"][series_name] = []
        
        posted_chapter_urls = state["chapters_posted"][series_name]
        chapters_to_post = [ch for ch in all_chapters_on_site if ch['url'] not in posted_chapter_urls]
        
        if not chapters_to_post:
            print(f"  - No new chapters to post for {series_name}.")
            continue
        
        for chapter in chapters_to_post:
            status, posted_url = create_chapter_post(blogger_service, series_name, chapter, config['selectors']['chapter_image'])
            
            if status == "QUOTA_EXCEEDED":
                print("\n--- Blogger API Quota Reached. Halting all operations. ---\n")
                return # সম্পূর্ণ বটটি বন্ধ হয়ে যাবে
            
            if status and posted_url:
                state["chapters_posted"][series_name].append(posted_url)
                save_state(state)
            
            time.sleep(30)
        time.sleep(120)

    print("\n--- Job finished. Waiting for the next schedule. ---")


if __name__ == '__main__':
    print("--- Bot Started on Koyeb ---")
    job() 
    schedule.every(6).hours.do(job)
    print("Scheduler is set up. Bot will now run every 6 hours.")
    while True:
        schedule.run_pending()
        time.sleep(60)
