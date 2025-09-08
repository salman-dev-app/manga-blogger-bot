# bot.py (v7 - The Ultimate Human Simulator Bot for CattBox)

import os
import json
import requests
from bs4 import BeautifulSoup
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import time
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
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
    """একটি হেডলেস Selenium Chrome ড্রাইভার সেটআপ করে"""
    print("  Setting up Selenium driver...")
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    try:
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
        print("  Selenium driver setup complete.")
        return driver
    except Exception as e:
        print(f"  Failed to set up Selenium driver: {e}")
        return None

def upload_image_to_cattbox_manually(driver, image_url, referer):
    """Selenium ব্যবহার করে CattBox-এ মানুষের মতো ছবি আপলোড করে"""
    try:
        print(f"    Downloading image to temp file: {image_url}")
        image_response = requests.get(image_url, headers={'User-Agent': 'Mozilla/5.0', 'Referer': referer}, timeout=60, stream=True)
        image_response.raise_for_status()

        # ছবিটি একটি অস্থায়ী ফাইলে সেভ করা হচ্ছে
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
            for chunk in image_response.iter_content(chunk_size=8192):
                tmp_file.write(chunk)
            temp_file_path = tmp_file.name

        print(f"    Uploading to CattBox from {temp_file_path}")
        driver.get("https://catbox.moe/")
        
        # "Select Files" ইনপুট ফিল্ডটি খুঁজে বের করে সেখানে ফাইলের পাথ দেওয়া হচ্ছে
        file_input = driver.find_element(By.ID, "fileToUpload")
        file_input.send_keys(temp_file_path)

        # আপলোড শেষ হওয়ার জন্য অপেক্ষা (এখানে আমরা আপলোড হওয়া ফাইলের লিঙ্কটি প্রদর্শিত হওয়ার জন্য অপেক্ষা করব)
        # CattBox আপলোড হওয়ার পর সরাসরি লিঙ্কটি পেজে দেখায়
        wait = WebDriverWait(driver, 120) # ১২০ সেকেন্ড পর্যন্ত অপেক্ষা
        # আপলোড হওয়া ফাইলের লিঙ্কটি সাধারণত একটি টেক্সটবক্সে বা সরাসরি বডিতে দেখা যায়
        # এই সিলেক্টরটি CattBox-এর গঠন অনুযায়ী পরিবর্তন হতে পারে
        uploaded_url_element = wait.until(EC.text_to_be_present_in_element_value((By.ID, 'catbox-url'), 'https://files.catbox.moe/'))
        
        uploaded_url = driver.find_element(By.ID, 'catbox-url').get_attribute('value')
        
        os.remove(temp_file_path) # অস্থায়ী ফাইলটি মুছে ফেলা হচ্ছে
        print(f"    CattBox upload successful: {uploaded_url}")
        return uploaded_url

    except Exception as e:
        print(f"    An error occurred during CattBox upload: {e}")
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        return None

# --- Main Post and Chapter Post Logic ---
def get_jikan_manga_details(series_name):
    # ... (এই ফাংশনটি আগের মতোই থাকবে) ...
    pass

def create_main_post(service, driver, series_name):
    print(f"  Main post for '{series_name}' does not exist. Creating it now...")
    details = get_jikan_manga_details(series_name)
    if not details: return False
    
    title = details.get('title', series_name)
    synopsis = details.get('synopsis', 'No synopsis available.')
    cover_url_original = details.get('images', {}).get('jpg', {}).get('large_image_url', '')
    if not cover_url_original: return False
        
    print("  Uploading cover image...")
    cover_url_cattbox = upload_image_to_cattbox_manually(driver, cover_url_original, 'https://myanimelist.net/')
    if not cover_url_cattbox:
        print("  Failed to upload cover image. Skipping main post creation.")
        return False
        
    # ... (বাকি পোস্ট তৈরির লজিক অপরিবর্তিত) ...
    pass

def scrape_chapters(series_config):
    # ... (এই ফাংশনটি আগের মতোই থাকবে) ...
    pass

def create_chapter_post(service, driver, series_name, chapter_info, image_selector):
    chapter_title, chapter_url = chapter_info['title'], chapter_info['url']
    print(f"\n- Processing Chapter: {chapter_title}")
    try:
        # ... (স্ক্র্যাপিং-এর অংশ অপরিবর্তিত) ...
        response = requests.get(chapter_url, headers={'User-agent': 'Mozilla/5.0'}, timeout=30)
        # ...
        image_tags = soup.select(image_selector)
        
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
            
            time.sleep(5) # প্রতিটি ছবির পর বিরতি
        
        # ... (বাকি পোস্ট তৈরির লজিক অপরিবর্তিত) ...
        pass
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
                # ... (বাকি লজিক অপরিবর্তিত) ...
            
            # ... (বাকি চ্যাপ্টার প্রসেসিং লজিক অপরিবর্তিত) ...
    
    finally:
        print("Closing Selenium driver.")
        driver.quit()

if __name__ == '__main__':
    main()
