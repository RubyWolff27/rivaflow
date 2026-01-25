# 🌐 RivaFlow Web App

Modern web interface for RivaFlow - the Training OS for the mat.

## ✨ Features

- **📱 Mobile-Responsive** - Works great on phone, tablet, and desktop
- **🎨 Modern UI** - Built with React, Tailwind CSS, and Lucide icons
- **📊 Interactive Charts** - Visualize your training data with Recharts
- **⚡ Fast & Local** - Runs entirely on your machine, no cloud required
- **🌙 Dark Mode Ready** - Prepared for dark mode support

## 🚀 Quick Start

### Prerequisites
- Python 3.11+ with RivaFlow installed
- Node.js 18+ and npm

### Start the Web App

```bash
# From the rivaflow root directory
./start-web.sh
```

This will:
1. Install frontend dependencies (first time only)
2. Start the FastAPI backend on `http://localhost:8000`
3. Start the React frontend on `http://localhost:5173`

Then open **http://localhost:5173** in your browser!

### Manual Start (Alternative)

**Terminal 1 - Backend:**
```bash
pip install -e .  # Install FastAPI deps
python -m uvicorn rivaflow.api.main:app --reload
```

**Terminal 2 - Frontend:**
```bash
cd web
npm install  # First time only
npm run dev
```

## 📱 Pages

- **Dashboard** - Quick stats, recent sessions, today's suggestion
- **Log Session** - Beautiful form for logging training (quick & full modes)
- **Reports** - Interactive analytics with charts and CSV export
- **Readiness** - Daily check-in with visual sliders
- **Techniques** - Track techniques and see stale ones
- **Videos** - Browse your instructional video library

## 🏗️ Tech Stack

**Frontend:**
- React 18 + TypeScript
- Vite (build tool)
- Tailwind CSS (styling)
- React Router (navigation)
- Recharts (charts)
- Lucide React (icons)
- Axios (API calls)

**Backend:**
- FastAPI (REST API)
- Uvicorn (ASGI server)
- Reuses all CLI services (zero duplication!)

## 📁 Structure

```
web/
├── src/
│   ├── pages/          # Page components
│   │   ├── Dashboard.tsx
│   │   ├── LogSession.tsx
│   │   ├── Reports.tsx
│   │   ├── Readiness.tsx
│   │   ├── Techniques.tsx
│   │   └── Videos.tsx
│   ├── components/     # Reusable components
│   │   └── Layout.tsx
│   ├── api/           # API client
│   │   └── client.ts
│   ├── types/         # TypeScript types
│   │   └── index.ts
│   ├── App.tsx        # Main app component
│   ├── main.tsx       # Entry point
│   └── index.css      # Global styles
├── package.json
├── vite.config.ts
├── tailwind.config.js
└── tsconfig.json
```

## 🔧 Development

**Frontend:**
```bash
cd web
npm run dev      # Start dev server
npm run build    # Build for production
npm run preview  # Preview production build
```

**Backend:**
```bash
# Auto-reload on code changes
uvicorn rivaflow.api.main:app --reload

# View API docs
open http://localhost:8000/docs
```

## 📱 Mobile Access

To access from your phone on the same network:

1. Find your computer's local IP (e.g., `192.168.1.100`)
2. Update `web/src/api/client.ts` - change `localhost` to your IP
3. Access from phone: `http://192.168.1.100:5173`

## 🎯 What Works

✅ All pages fully functional
✅ Mobile-responsive design
✅ Session logging with autocomplete
✅ Reports with interactive charts
✅ Readiness tracking with sliders
✅ Techniques management
✅ Videos library
✅ CSV export
✅ Real-time data updates

## 🚧 What's Next (Optional)

- Dark mode toggle
- More chart types
- Offline mode with service worker
- Push notifications for training reminders
- Video embedding (YouTube player)
- Technique progress visualization

## 💾 Data

All data is stored in the same SQLite database as the CLI:
- Location: `~/.rivaflow/rivaflow.db`
- CLI and web app share the same data
- Use whichever interface you prefer!

## 🐛 Troubleshooting

**Frontend won't start:**
```bash
cd web
rm -rf node_modules package-lock.json
npm install
```

**Backend errors:**
```bash
pip install -e . --force-reinstall
```

**CORS errors:**
Make sure the backend is running on port 8000 and frontend on 5173.

## 📄 License

MIT - Same as RivaFlow CLI

---

**Train with intent. Flow to mastery.** 🥋
