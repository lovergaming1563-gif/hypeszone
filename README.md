# 🚀 Telegram Support Inbox Bot

A production-ready Telegram Support system that transforms your Telegram Group into a fully functional Helpdesk/Inbox. It features an asynchronous architecture, database storage (SQLite/PostgreSQL ready), Analytics, User Ratings, and a FastAPI integration for health checks & Uptime monitors.

## 🌟 Features
*   **User Inbox:** Send Text, Photos, Videos, Documents, and Voice Notes.
*   **Admin Dashboard:** Group-based ticket management. Reply, Close, Ban, and prioritize directly via Inline Buttons.
*   **Rating System:** Users can rate their support experience 1-5 Stars.
*   **Analytics:** Track open chats, closed chats, total users, and total messages.
*   **Web Server:** Built-in FastAPI server exposing `/health` and `/ping` for Render and UptimeRobot integration.
*   **Modular Architecture:** Easily scalable and maintainable.

---

## 🛠 Local Setup Instructions

**Python Version Support:**
*   **Recommended:** Python 3.12 or 3.13
*   **Minimum:** Python 3.10
*   *Note: This project is optimized for Python 3.13 and provides pre-built binaries for all dependencies (no Rust or C++ compilers required).*

**1. Clone or Extract the Project**
Navigate to the project folder.

**2. Create a Virtual Environment**
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
```

**3. Install Dependencies**
```bash
pip install -r requirements.txt
```

**4. Configuration**
Rename `.env.example` to `.env` and configure your variables:
```env
BOT_TOKEN=your_bot_token_from_botfather
ADMIN_GROUP_ID=-100xxxxxxxxxxx # Ensure this starts with -100 for supergroups
DATABASE_URL=sqlite+aiosqlite:///support_bot.db
PORT=8080
```
*(To find your `ADMIN_GROUP_ID`, add your bot to the group, send a message, and use an ID bot or print the update in console)*.

**5. Run the Bot**
```bash
python main.py
```
You should see `Bot Started Successfully` in the console.

---

## ☁️ Deployment on Render

This bot is natively configured to run on Render without code changes because it binds to the port provided by Render's environment.

**1. Create a New Web Service on Render**
*   Connect your GitHub repository.
*   **Build Command:** `pip install -r requirements.txt`
*   **Start Command:** `python main.py`

**2. Add Environment Variables**
In the Render dashboard, go to your service settings -> Environment:
*   `PYTHON_VERSION` = `3.10` (or higher)
*   `BOT_TOKEN` = `your_token`
*   `ADMIN_GROUP_ID` = `your_group_id`
*   `DATABASE_URL` = (Optional: Provide your PostgreSQL database URL, e.g., `postgresql://...`. The bot auto-converts it to `postgresql+asyncpg://`).

**3. Keep-Alive / Uptime Monitoring**
Render spins down free web services after 15 minutes of inactivity. To prevent this:
1. Create a free account on [UptimeRobot](https://uptimerobot.com/).
2. Add a new HTTP(s) Monitor pointing to your Render URL: `https://your-app.onrender.com/ping`
3. Set the interval to 5 minutes. The bot will now stay awake 24/7!

---

## 👨‍💻 Usage

### For Users
Users simply search for your Bot username and press `/start`. They will see a rich Reply Keyboard with options to send a message, view FAQs, etc. Sending a message instantly opens a ticket.

### For Admins
Add the bot to your designated Admin Group and grant it admin permissions (so it can read and delete messages if necessary).
When a user sends a ticket, it appears as a formatted card in the group.
1. Click **Reply**.
2. **Important:** Your Telegram app will auto-select the Bot's prompt message. Type your reply and hit send. The Bot catches this specific reply and forwards it to the User!
3. Use `/stats` in the group to see analytics.
