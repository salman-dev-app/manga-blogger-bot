import os
from dotenv import load_dotenv

load_dotenv()

BLOG_ID = os.getenv('BLOG_ID')
IMGBB_API_KEY = os.getenv('IMGBB_API_KEY') # এটি এখন আর ব্যবহৃত হচ্ছে না, তবে রেখে দিতে পারেন
CONFIG_FILE = 'config.json'
STATE_FILE = 'posted_chapters.json' # এটিও এখন আর ব্যবহৃত হবে না
SCOPES = ['https://www.googleapis.com/auth/blogger']
G_CLIENT_ID = os.getenv('G_CLIENT_ID')
G_CLIENT_SECRET = os.getenv('G_CLIENT_SECRET')
G_REFRESH_TOKEN = os.getenv('G_REFRESH_TOKEN')

# MongoDB Configuration
MONGO_URI = os.getenv('MONGO_URI')

# Cloudinary Configuration
CLOUDINARY_CLOUD_NAME = os.getenv('CLOUDINARY_CLOUD_NAME')
CLOUDINARY_API_KEY = os.getenv('CLOUDINARY_API_KEY')
CLOUDINARY_API_SECRET = os.getenv('CLOUDINARY_API_SECRET')
