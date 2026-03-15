<div align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&color=0:FF6B6B,100:4ECDC4&height=200&text=Manga%20Blogger%20Bot&fontSize=50&fontColor=fff&animation=fadeIn&fontAlignY=40&desc=Automated%20Manga%20Publishing%20System&descAlignY=55&descSize=15"/>
</div>

<p align="center">
  <a href="https://github.com/salman-dev-app/manga-blogger-bot">
    <img src="https://readme-typing-svg.demolab.com?font=Tagesschrift&size=25&duration=2000&pause=800&color=F7F7F7&background=FF001400&center=true&vCenter=true&multiline=true&width=500&height=80&lines=Automated+Manga+Scraping;Seamless+Blogger+Integration;Auto+Publish+Chapters+Instantly" alt="Typing SVG" />
  </a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Version-1.0.0-FF6B6B?style=for-the-badge&logo=semver&logoColor=white" />
  <img src="https://img.shields.io/github/last-commit/salman-dev-app/manga-blogger-bot/main?style=for-the-badge&color=00D9FF&label=LAST%20UPDATED&logo=github&logoColor=white" />
  <img src="https://img.shields.io/badge/Platform-Blogger_API-4ECDC4?style=for-the-badge&logo=blogger&logoColor=white" />
</p>

---

<div align="center">
  <h3>
    <img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Smilies/Robot.png" alt="Robot" width="25" height="25" style="vertical-align: middle;" /> 
    A powerful bot that automates fetching manga chapters and publishing them directly to your Google Blogger (Blogspot) website.
  </h3>
</div>

---

## <img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Objects/Open%20Book.png" alt="Book" width="30" height="30" style="vertical-align: middle;" /> Features & Capabilities

<div align="center">

### Core Automation

</div>

<p><img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Symbols/Check%20Mark%20Button.png" width="18" height="18" style="vertical-align: middle;" /> <strong>Auto-Scraping</strong> - Automatically fetches the latest manga chapters and high-quality images from target sources.</p>
<p><img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Symbols/Check%20Mark%20Button.png" width="18" height="18" style="vertical-align: middle;" /> <strong>Blogger API Integration</strong> - Seamlessly connects to your Blogger site using Google OAuth2.0 / Service Accounts.</p>
<p><img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Symbols/Check%20Mark%20Button.png" width="18" height="18" style="vertical-align: middle;" /> <strong>Smart Image Hosting</strong> - Processes and uploads images directly into Blogger HTML format.</p>
<p><img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Symbols/Check%20Mark%20Button.png" width="18" height="18" style="vertical-align: middle;" /> <strong>Custom HTML Templates</strong> - Wraps manga chapters in a responsive, reading-friendly HTML layout automatically.</p>
<p><img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Symbols/Check%20Mark%20Button.png" width="18" height="18" style="vertical-align: middle;" /> <strong>Cron Job Scheduling</strong> - Set intervals (e.g., every 1 hour) to check for and post new manga updates unattended.</p>

---

## <img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Objects/Wrench.png" alt="Wrench" width="30" height="30" style="vertical-align: middle;" /> Technology Stack

<div align="center">
  <img src="https://skillicons.dev/icons?i=nodejs,js,python,git,github,google&theme=dark" />
</div>

---

## <img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Objects/File%20Folder.png" alt="Folder" width="30" height="30" style="vertical-align: middle;" /> Prerequisites & Setup

Before installing the bot, ensure you have the following ready:

1. **Google Cloud Console Setup:**
   - Go to[Google Cloud Console](https://console.cloud.google.com/).
   - Enable the **Blogger API v3**.
   - Generate **OAuth 2.0 Client IDs** or a **Service Account JSON** file.
2. **Environment Ready:**
   - Node.js installed (v16.x or higher) OR Python (v3.8+) depending on your execution environment.
   - Git installed on your system.
3. **Target Blogger Setup:**
   - Create a Blogspot website.
   - Copy your `BLOG_ID` (Found in your Blogger dashboard URL).

---

## <img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Travel%20and%20places/Rocket.png" alt="Rocket" width="30" height="30" style="vertical-align: middle;" /> Installation Guide

Follow these simple steps to deploy the Manga Blogger Bot on your local machine or server.

<details open>
<summary><strong><img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Objects/Desktop%20Computer.png" alt="Computer" width="20" height="20" style="vertical-align: middle;" /> Step-by-Step Instructions (Click to Collapse)</strong></summary>

<br/>

**1. Clone the Repository**
```bash
git clone https://github.com/salman-dev-app/manga-blogger-bot.git
cd manga-blogger-bot
```

**2. Install Dependencies**
```bash
# If using Node.js:
npm install

# If using Python:
pip install -r requirements.txt
```

**3. Configure Environment Variables**
Rename `.env.example` to `.env` and fill in your details:
```bash
cp .env.example .env
```

</details>

---

## <img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Objects/Locked.png" alt="Lock" width="30" height="30" style="vertical-align: middle;" /> Environment Variables (`.env`)

To make the bot function, correctly input your credentials inside the `.env` file:

```ini
# Google API & Blogger Configuration
CLIENT_ID=your_google_client_id_here
CLIENT_SECRET=your_google_client_secret_here
REFRESH_TOKEN=your_google_refresh_token
BLOG_ID=1234567890123456789

# Bot Settings
SCRAPE_SOURCE_URL=https://target-manga-site.com/
POST_STATUS=live  # Set to 'draft' to review posts before publishing
CRON_SCHEDULE="0 * * * *" # Runs every 1 hour
```

---

## <img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Objects/Gear.png" alt="Gear" width="30" height="30" style="vertical-align: middle;" /> Execution & Usage

Once your `.env` is set up and authenticated, you can start the bot!

**To run a single sync manual check:**
```bash
npm run start
# OR python main.py
```

**To start the bot in background scheduling (Cron mode):**
```bash
npm run cron
# OR python cron.py
```

> **Note:** The bot will log its progress in the terminal. If a chapter already exists on your blog, it will automatically skip it to prevent duplicate posting!

---

## <img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Symbols/Warning.png" alt="Warning" width="30" height="30" style="vertical-align: middle;" /> Disclaimer

<div align="center">
  <blockquote>
    This bot is created for educational and automation purposes only. Web scraping and automated posting must comply with the Terms of Service of the targeted sources and Google's Developer Policies. The developer takes no responsibility for blocked accounts or copyright strikes resulting from the misuse of this tool.
  </blockquote>
</div>

---

<div align="center">
  <h2>
    <img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Activities/Party%20Popper.png" alt="Party" width="30" height="30" style="vertical-align: middle;" /> 
    Connect with the Developer
  </h2>
  
  <p>Encountered a bug or want to request a feature? Feel free to connect!</p>
</div>

<p align="center">
  <a href="https://github.com/salman-dev-app/manga-blogger-bot/issues">
    <img src="https://img.shields.io/badge/Report_Issue-GitHub-FF6B6B?style=for-the-badge&logo=github&logoColor=white" />
  </a>
  <a href="https://wa.me/8801840933137">
    <img src="https://img.shields.io/badge/WhatsApp-Direct_Chat-4ECDC4?style=for-the-badge&logo=whatsapp&logoColor=white" />
  </a>
</p>

---

<div align="center">
  <h2>
    <img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Smilies/Heart%20with%20Ribbon.png" alt="Heart" width="30" height="30" style="vertical-align: middle;" /> 
    Support the Project
  </h2>
  <p>⭐ Don't forget to <b>Star</b> this repository if it helped you automate your manga blog!</p>
</div>

---

## <img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Objects/Scroll.png" alt="Scroll" width="30" height="30" style="vertical-align: middle;" /> License

<div align="center">
  <a href="LICENSE">
    <img src="https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge&logo=open-source-initiative&logoColor=white" />
  </a>
</div>

<p align="center">
  This project is licensed under the MIT License - see the <a href="LICENSE">LICENSE</a> file for details.
</p>

---

<footer align="center">
  <p>© 2024-2026 Manga Blogger Bot • All rights reserved</p>
  <p>
    Status: 
    <a href="https://github.com/salman-dev-app/manga-blogger-bot">
      <img src="https://img.shields.io/badge/Systems-Online-4ECDC4?style=flat" alt="Status" style="vertical-align: middle;">
    </a>
  </p>
  <p>Engineered by <a href="https://github.com/salman-dev-app">Md Salman Biswas</a></p>
</footer>

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:FF6B6B,100:4ECDC4&height=120&section=footer"/>
