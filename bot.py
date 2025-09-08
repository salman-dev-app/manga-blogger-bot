# bot.py (v7.5 - The Ultimate Human Simulator Bot - CattBox Spelling Fix)

import os
import json
import requests
from bs4 import BeautifulSoup
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import time
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import tempfile

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

def setup_selenium_driver():
    print("  Setting up Selenium driver...")
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36")
    try:
        driver = webdriver.Chrome(options=options)
        print("  Selenium driver setup complete.")
        return driver
    except Exception as e:
        print(f"  Failed to set up Selenium driver: {e}"); return None

def upload_image_to_cattbox_manually(driver, image_url, referer):
    temp_file_path = None
    try:
        print(f"    Downloading image to temp file: {image_url}")
        image_response = requests.get(image_url, headers={'User-Agent': 'Mozilla/5.0', 'Referer': referer}, timeout=60, stream=True)
        image_response.raise_for_status()

        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
            for chunk in image_response.iter_content(chunk_size=8192):
                tmp_file.write(chunk)
            temp_file_path = tmp_file.name

        print(f"    Uploading to Catbox.moe from {temp_file_path}")
        # --- সঠিক URL টি এখানে ---
        driver.get("https://catbox.moe/")
        
        file_input = driver.find_element(By.CSS_SELECTOR, "input[type='file']")
        
        driver.execute_script("arguments[0].style.display = 'block';", file_input)
        file_input.send_keys(temp_file_path)

        wait = WebDriverWait(driver, 120)
        wait.until(EC.text_to_be_present_in_element((By.TAG_NAME, 'body'), 'https://files.catbox.moe/'))
        
        uploaded_url = driver.find_element(By.TAG_NAME, 'body').text.strip()
        
        os.remove(temp_file_path)
        
        # নিশ্চিত করুন যে শুধুমাত্র URL টিই ফেরত যাচ্ছে
        if uploaded_url.startswith("https://files.catbox.moe/"):
            print(f"    CattBox upload successful: {uploaded_url}")
            return uploaded_url
        else:
            print(f"    Failed to parse CattBox URL from response: {uploaded_url}")
            return None

    except Exception as e:
        print(f"    An error occurred during CattBox upload: {e}")
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
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

def create_main_post(service, driver, series_name):
    print(f"  Creating main post for '{series_name}'...")
    details = get_jikan_manga_details(series_name)
    if not details: return False
    
    title = details.get('title', series_name)
    synopsis = details.get('synopsis', 'No synopsis available.')
    cover_url_original = details.get('images', {}).get('jpg', {}).get('large_image_url', '')
    if not cover_url_original: return False
        
    print("    Uploading cover image via CattBox...")
    cover_url_final = upload_image_to_cattbox_manually(driver, cover_url_original, 'https://myanimelist.net/')
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

def create_chapter_post(service, driver, series_name, chapter_info, image_selector):
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
            cattbox_url = upload_image_to_cattbox_manually(driver, img_url, chapter_url)
            
            if cattbox_url:
                html_content += f'<div class="separator" style="text-align: center;"><img src="{cattbox_url}" /></div>\n'
            else:
                print("    Image upload failed. Skipping this image.")
            time.sleep(5)
        
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
    driver = setup_selenium_driver()

    if not blogger_service or not driver:
        if driver: driver.quit()
        print("Could not initialize services. Exiting.")
        return

    try:
        for config in configs:
            series_name = config['name']
            print(f"\n--- Processing Series: {series_name} ---")
            
            if series_name not in state["main_posts_created"]:
                success = create_main_post(blogger_service, driver, series_name)
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
                success, posted_url = create_chapter_post(blogger_service, driver, series_name, chapter, config['selectors']['chapter_image'])
                if success and posted_url:
                    state["chapters_posted"][series_name].append(posted_url)
                    save_json(STATE_FILE, state)
                time.sleep(30)
            time.sleep(120)
    
    finally:
        print("Closing Selenium driver.")
        driver.quit()

if __name__ == '__main__':
    main()
