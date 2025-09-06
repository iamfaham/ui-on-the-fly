# 🎨 UI on the Fly

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.95+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Deploy on Render](https://img.shields.io/badge/deploy%20on-render-46E3B7.svg)](https://render.com)

> A powerful FastAPI application that generates beautiful, dynamic UIs using AI models. Each request creates a unique, responsive web interface with modern design elements.

## ✨ Features

- 🎨 **Dynamic UI Generation**: Creates unique UIs on every request
- 🤖 **AI-Powered**: Uses Cerebras API with multiple model options
- 📱 **Responsive Design**: All generated UIs are mobile-friendly
- ⚡ **Fast API**: Built with FastAPI for high performance
- 🔒 **Rate Limiting**: Built-in protection against abuse
- 🎛️ **Admin Panel**: Custom UI generation interface
- 📊 **History Tracking**: Keeps track of generated UIs
- 🚀 **Easy Deployment**: One-click deployment on Render
- 📈 **Real-time Monitoring**: Health checks and logging

## 🖼️ Demo

> **Note**: Add screenshots or GIFs here to showcase the generated UIs

<!--
![Demo GIF](docs/demo.gif)
![Generated UI Example](docs/ui-example.png)
-->

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- [Cerebras API Key](https://cloud.cerebras.ai/)
- Git

### Installation

1. **Clone the repository**:

   ```bash
   git clone https://github.com/iamfaham/ui-on-the-fly.git
   cd ui--on-the-fly
   ```

2. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:

   ```bash
   # Create a .env file
   echo "CEREBRAS_API_KEY=your_api_key_here" > .env
   ```

4. **Run the application**:

   ```bash
   python main.py
   ```

5. **Access the application**:
   - Main generator: http://localhost:8000
   - Admin panel: http://localhost:8000/admin
   - API docs: http://localhost:8000/docs

## 📚 API Documentation

### Endpoints

| Method | Endpoint        | Description                       |
| ------ | --------------- | --------------------------------- |
| `GET`  | `/`             | Generate a random UI              |
| `POST` | `/api/generate` | Generate UI with custom prompt    |
| `GET`  | `/admin`        | Admin panel for custom generation |
| `GET`  | `/api/history`  | View generation history           |
| `GET`  | `/api/models`   | List available models             |
| `GET`  | `/health`       | Health check endpoint             |
| `GET`  | `/docs`         | Interactive API documentation     |

### Usage Examples

#### Generate a Random UI

```bash
curl http://localhost:8000/
```

#### Generate UI with Custom Prompt

```bash
curl -X POST "http://localhost:8000/api/generate" \
     -H "Content-Type: application/json" \
     -d '{
       "prompt": "Create a modern dashboard for a fitness app",
       "model": "qwen-3-coder-480b",
       "temperature": 0.8
     }'
```

#### Check Available Models

```bash
curl http://localhost:8000/api/models
```

#### View Generation History

```bash
curl http://localhost:8000/api/history
```

## 🚀 Deployment

### Deploy on Render (Recommended)

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

#### Prerequisites

1. A [Render](https://render.com) account
2. A Cerebras API key
3. Your code pushed to a Git repository (GitHub, GitLab, or Bitbucket)

### Step-by-Step Deployment

#### Method 1: Using render.yaml (Recommended)

1. **Push your code to Git**:

   ```bash
   git add .
   git commit -m "Add deployment configuration"
   git push origin main
   ```

2. **Connect to Render**:

   - Go to [Render Dashboard](https://dashboard.render.com)
   - Click "New +" → "Blueprint"
   - Connect your Git repository
   - Render will automatically detect the `render.yaml` file

3. **Set Environment Variables**:

   - In the Render dashboard, go to your service
   - Navigate to "Environment" tab
   - Add `CEREBRAS_API_KEY` with your actual API key
   - The `PORT` variable is already configured in render.yaml

4. **Deploy**:
   - Click "Create Blueprint"
   - Render will automatically build and deploy your application

#### Method 2: Manual Setup

1. **Create a new Web Service**:

   - Go to [Render Dashboard](https://dashboard.render.com)
   - Click "New +" → "Web Service"
   - Connect your Git repository

2. **Configure the service**:

   - **Name**: `ui-generator` (or your preferred name)
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python main.py`
   - **Plan**: Free (or choose a paid plan for better performance)

3. **Set Environment Variables**:

   - `CEREBRAS_API_KEY`: Your Cerebras API key
   - `PORT`: `10000` (Render's default port)

4. **Deploy**:
   - Click "Create Web Service"
   - Wait for the build to complete

## ⚙️ Configuration

### Environment Variables

| Variable           | Description                               | Required | Default |
| ------------------ | ----------------------------------------- | -------- | ------- |
| `CEREBRAS_API_KEY` | Your Cerebras API key for AI model access | ✅ Yes   | -       |
| `PORT`             | Port number for the application           | ❌ No    | `8000`  |
| `REDIS_URL`        | Redis URL for caching (optional)          | ❌ No    | -       |
| `DATABASE_URL`     | Database URL for persistence (optional)   | ❌ No    | -       |

### Getting a Cerebras API Key

1. Visit [Cerebras Cloud](https://cloud.cerebras.ai/)
2. Sign up for an account
3. Navigate to the API section
4. Generate a new API key
5. Copy the key and add it to your environment variables

## 📁 Project Structure

```
ui-generator/
├── main.py              # FastAPI application
├── requirements.txt     # Python dependencies
├── render.yaml         # Render deployment configuration
├── pyproject.toml      # Project configuration
├── templates/          # HTML templates
│   └── admin.html      # Admin panel template
├── .env                # Environment variables (create this)
├── .gitignore          # Git ignore rules
└── README.md           # This file
```

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes** and test them locally
4. **Commit your changes**: `git commit -m 'Add some amazing feature'`
5. **Push to the branch**: `git push origin feature/amazing-feature`
6. **Open a Pull Request**

### Development Setup

```bash
# Clone your fork
git clone https://github.com/iamfaham/ui-on-the-fly.git
cd ui-generator

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your API key

# Run tests (if available)
python -m pytest

# Start development server
python main.py
```

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) for the amazing web framework
- [Cerebras](https://www.cerebras.net/) for providing the AI models
- [Render](https://render.com/) for easy deployment

## 📞 Support

If you have any questions or need help:

- 📧 Open an [issue](https://github.com/iamfaham/ui-on-the-fly/issues)
- 💬 Start a [discussion](https://github.com/iamfaham/ui-on-the-fly/discussions)
