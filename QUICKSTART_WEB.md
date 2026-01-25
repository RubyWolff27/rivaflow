# 🚀 RivaFlow Web App - Quick Start Guide

## What You Got

A complete, modern web application for tracking your BJJ/grappling training:
- 📱 **Mobile-responsive** - Works on phone, tablet, desktop
- 🎨 **Beautiful UI** - Modern design with Tailwind CSS
- 📊 **Interactive charts** - Visualize your progress
- 🔒 **100% Local** - All data stays on your machine
- ⚡ **Fast** - React + FastAPI

## Start the App (3 Steps)

### 1. Install Dependencies

```bash
cd /Users/rubertwolff/scratch

# Install Python API dependencies
pip install -e .

# Install frontend dependencies (first time only)
cd web
npm install
cd ..
```

### 2. Start the Servers

**Easy Way (Recommended):**
```bash
./start-web.sh
```

**Manual Way (if you prefer separate terminals):**

Terminal 1 - Backend:
```bash
python -m uvicorn rivaflow.api.main:app --reload
```

Terminal 2 - Frontend:
```bash
cd web
npm run dev
```

### 3. Open Your Browser

Navigate to: **http://localhost:5173**

You should see the RivaFlow dashboard! 🎉

## 📱 What You Can Do

### Dashboard (`/`)
- View quick stats
- See recent sessions
- Get today's training recommendation

### Log Session (`/log`)
- Full session logging form
- Autocomplete for gyms, locations, partners
- Mobile-friendly inputs

### Reports (`/reports`)
- Week/month analytics
- Interactive charts
- CSV export
- Submission statistics

### Readiness (`/readiness`)
- Daily check-in with sliders
- Track sleep, stress, soreness, energy
- Visual composite score

### Techniques (`/techniques`)
- Add and track techniques
- See stale techniques (7+ days)
- Categories: guard, pass, submission, etc.

### Videos (`/videos`)
- Browse instructional videos
- See linked techniques
- Timestamps for key moments

## 📱 Access from Phone

Want to use it on your phone while training?

1. Find your computer's IP address:
   ```bash
   # Mac/Linux:
   ifconfig | grep "inet "

   # Example: 192.168.1.100
   ```

2. Update the API URL:
   - Edit `web/src/api/client.ts`
   - Change `localhost` to your IP (e.g., `192.168.1.100`)

3. On your phone, open: `http://192.168.1.100:5173`

Make sure your phone is on the same WiFi network!

## 🎯 Quick Test

1. **Log a session:**
   - Click "Log Session"
   - Fill in: gym name, class type (gi/no-gi), rolls
   - Click "Log Session"
   - Redirects to dashboard with your new session!

2. **Check readiness:**
   - Click "Readiness"
   - Adjust sliders for sleep, stress, soreness, energy
   - Click "Log Readiness"
   - See your composite score!

3. **View reports:**
   - Click "Reports"
   - Toggle between Week/Month
   - See charts and statistics
   - Export to CSV if desired

## 🐛 Troubleshooting

**"Cannot GET /"** - Frontend isn't running
```bash
cd web
npm run dev
```

**"Network Error"** - Backend isn't running
```bash
python -m uvicorn rivaflow.api.main:app --reload
```

**npm install fails** - Try clearing cache:
```bash
cd web
rm -rf node_modules package-lock.json
npm install
```

**Port already in use:**
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Kill process on port 5173
lsof -ti:5173 | xargs kill -9
```

## 🔗 Useful URLs

- **Web App:** http://localhost:5173
- **API:** http://localhost:8000
- **API Docs (Swagger):** http://localhost:8000/docs
- **API Redoc:** http://localhost:8000/redoc

## 📊 Architecture

```
┌─────────────────┐
│  React Frontend │  Port 5173
│  (Vite + TS)    │
└────────┬────────┘
         │ HTTP
         ▼
┌─────────────────┐
│  FastAPI        │  Port 8000
│  (REST API)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Service Layer  │  (Reused from CLI)
│  Business Logic │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  SQLite DB      │  ~/.rivaflow/rivaflow.db
│  (Local)        │
└─────────────────┘
```

## 💡 Tips

1. **Use the web app on your phone** at the gym for quick logging
2. **Keep both interfaces** - Use web for visual stuff, CLI for scripts
3. **Data is shared** - Everything you log in web appears in CLI and vice versa
4. **Export your data** - Use CSV export from Reports page regularly
5. **Dark mode** - The UI is ready for dark mode (just needs toggle)

## 🎉 You're Ready!

Open http://localhost:5173 and start tracking your training!

**Train with intent. Flow to mastery.** 🥋
