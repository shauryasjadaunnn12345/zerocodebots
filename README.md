<h1 align="center">🚀 ZeroCodeBots</h1>

<p align="center">
  <b>Build, embed, and analyze AI chatbots — without writing a single line of code.</b>
</p>

<p align="center">
  <img src="https://readme-typing-svg.herokuapp.com?font=Fira+Code&size=24&duration=3000&pause=1000&color=00F7FF&center=true&vCenter=true&width=700&lines=No-Code+AI+Chatbot+Builder;Build+%2C+Embed+%26+Analyze+Chatbots;AI+Powered+%7C+Analytics+Driven;Deployed+on+Render" />
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Status-Live-success?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Platform-No--Code-blue?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Backend-Django-darkgreen?style=for-the-badge&logo=django" />
  <img src="https://img.shields.io/badge/Frontend-JavaScript-yellow?style=for-the-badge&logo=javascript" />
  <img src="https://img.shields.io/badge/Deployment-Render-purple?style=for-the-badge&logo=render" />
  <img src="https://img.shields.io/github/license/shauryasjadaunnn12345/zerocodebots?style=for-the-badge" />
  <img src="https://img.shields.io/github/stars/shauryasjadaunnn12345/zerocodebots?style=for-the-badge" />
</p>

<p align="center">
  <a href="#-demo">Demo</a> •
  <a href="#-features">Features</a> •
  <a href="#-tech-stack">Tech Stack</a> •
  <a href="#-getting-started">Getting Started</a> •
  <a href="#-tutorial">Tutorial</a> •
  <a href="#-roadmap">Roadmap</a> •
  <a href="#-contributing">Contributing</a>
</p>

---

## 🌟 About

**ZeroCodeBots** is a no-code platform for building, deploying, and monitoring AI-powered chatbots. Create a Q&A chatbot in minutes, drop one line of JavaScript into any website, and watch conversations roll in on a live analytics dashboard — no engineering required.

Built for startups, students, small businesses, agencies, and creators who want automation without the complexity.

## 🎥 Demo

https://github.com/user-attachments/assets/7a4fc6ee-fd8d-4074-85af-5f144206e4ee

---

## ✨ Features

| Feature | Description |
|---|---|
| 🤖 **No-Code Chatbot Builder** | Create chatbot responses with simple Q&A input fields — no scripting needed |
| 🌐 **One-Line Embed** | Copy a single JavaScript snippet to add your chatbot to any website |
| 📊 **Analytics Dashboard** | Track conversations, user queries, engagement, and FAQs in real time |
| 🔄 **Instant Updates** | Edit responses anytime — changes go live without redeployment |
| 🧠 **AI-Based Conversation Handling** | Natural, context-aware replies powered by AI |
| 🔐 **Secure & Scalable** | Django backend with structured REST APIs |

---

## 🛠 Tech Stack

<p align="center">
  <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/html5/html5-original.svg" height="50"/>&nbsp;&nbsp;
  <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/css3/css3-original.svg" height="50"/>&nbsp;&nbsp;
  <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/javascript/javascript-original.svg" height="50"/>&nbsp;&nbsp;
  <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/django/django-plain.svg" height="50"/>&nbsp;&nbsp;
  <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/python/python-original.svg" height="50"/>&nbsp;&nbsp;
  <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/postgresql/postgresql-original.svg" height="50"/>
</p>

| Layer | Technology |
|---|---|
| **Frontend** | HTML5, CSS3, JavaScript |
| **Backend** | Django, Django REST Framework, Python |
| **Database** | SQLite (dev) / PostgreSQL (prod) |
| **Hosting** | Render |

---

## 📂 Project Structure

```
zerocodebots/
├── backend/
│   ├── chatbots/          # Chatbot models, views, serializers
│   ├── analytics/         # Analytics tracking & dashboard APIs
│   └── manage.py
├── frontend/
│   ├── static/             # CSS, JS, embed script
│   └── templates/          # HTML templates
├── requirements.txt
└── README.md
```

> Adjust this tree to match your actual repo layout.

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- pip
- (Optional) PostgreSQL for production

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/shauryasjadaunnn12345/zerocodebots.git
cd zerocodebots

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Apply migrations
python manage.py migrate

# 5. Run the development server
python manage.py runserver
```

The app will be available at `http://127.0.0.1:8000/`.

### Environment Variables

Create a `.env` file in the project root:

```env
SECRET_KEY=your-django-secret-key
DEBUG=True
DATABASE_URL=postgres://user:password@localhost:5432/zerocodebots
```

---

## 📘 Tutorial

### Step 1 — Create a Project
<p align="center">
  <img src="https://github.com/user-attachments/assets/cbc37d7e-7f78-48b3-84b4-169f579419b8" width="800"/>
</p>

### Step 2 — Create or Edit a Project
<p align="center">
  <img src="https://github.com/user-attachments/assets/cd2710c6-3a84-40ea-b1cb-7913181db34b" width="800"/>
</p>

### Step 3 — Name Your Project
<p align="center">
  <img src="https://github.com/user-attachments/assets/6d0cb2d0-cbf4-4d00-86bd-7f92b1811a5c" width="800"/>
</p>

### Step 4 — Create Question & Answer Prompts
<p align="center">
  <img src="https://github.com/user-attachments/assets/f0d96043-6559-49f5-a6b6-a8bdae249697" width="800"/>
</p>

### Step 5 — Test Your Chatbot
<p align="center">
  <img src="https://github.com/user-attachments/assets/c3ad6662-aa60-4a05-93cc-5685c5758b67" width="800"/>
</p>

### Step 6 — Embed the Chatbot in Your Website
<p align="center">
  <img width="900" alt="Embed code screenshot" src="https://github.com/user-attachments/assets/a488361d-6d84-4588-986c-17c18fd8b27f" />
</p>

### Step 7 — View Chatbot Analytics
<p align="center">
  <img width="900" alt="Analytics dashboard screenshot" src="https://github.com/user-attachments/assets/54ef9f25-9bf8-4e58-8128-5eeb6a039c0c" />
</p>

---

## 🗺 Roadmap

- [ ] Multi-language chatbot support
- [ ] Team/workspace collaboration
- [ ] Slack & WhatsApp integrations
- [ ] Custom AI model plug-ins
- [ ] Advanced analytics (sentiment, drop-off funnels)

> Have an idea? [Open an issue](https://github.com/shauryasjadaunnn12345/zerocodebots/issues) or start a discussion.

---

## 🤝 Contributing

Contributions are welcome!

1. Fork the repo
2. Create a branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m "Add your feature"`
4. Push to the branch: `git push origin feature/your-feature`
5. Open a Pull Request

Please open an issue first for major changes so we can discuss what you'd like to do.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

## 🙋 Support

If you find a bug or have a feature request, please [open an issue](https://github.com/shauryasjadaunnn12345/zerocodebots/issues).

<p align="center">Made with ❤️ by <a href="https://github.com/shauryasjadaunnn12345">Shaurya</a></p>
