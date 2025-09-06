# UI Generator

A FastAPI application that generates beautiful, dynamic UIs using AI models via the Cerebras API. Each request creates a unique, responsive web interface with modern design elements.

## Features

- 🎨 **Dynamic UI Generation**: Creates unique UIs on every request
- 🤖 **AI-Powered**: Uses Cerebras API with multiple model options
- 📱 **Responsive Design**: All generated UIs are mobile-friendly
- ⚡ **Fast API**: Built with FastAPI for high performance
- 🔒 **Rate Limiting**: Built-in protection against abuse
- 🎛️ **Admin Panel**: Custom UI generation interface
- 📊 **History Tracking**: Keeps track of generated UIs

## API Endpoints

- `GET /` - Generate a random UI
- `POST /api/generate` - Generate UI with custom prompt
- `GET /admin` - Admin panel for custom generation
- `GET /api/history` - View generation history
- `GET /api/models` - List available models
- `GET /health` - Health check endpoint

## Deployment on Render

### Prerequisites

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

### Environment Variables

| Variable           | Description                                     | Required |
| ------------------ | ----------------------------------------------- | -------- |
| `CEREBRAS_API_KEY` | Your Cerebras API key for AI model access       | Yes      |
| `PORT`             | Port number for the application (default: 8000) | No       |

### Getting a Cerebras API Key

1. Visit [Cerebras Cloud](https://cloud.cerebras.ai/)
2. Sign up for an account
3. Navigate to the API section
4. Generate a new API key
5. Copy the key and add it to your Render environment variables

### Local Development

1. **Clone the repository**:

   ```bash
   git clone <your-repo-url>
   cd ui-generator
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

### Project Structure

```
ui-generator/
├── main.py              # FastAPI application
├── requirements.txt     # Python dependencies
├── render.yaml         # Render deployment configuration
├── pyproject.toml      # Project configuration
├── templates/          # HTML templates
│   └── admin.html      # Admin panel template
└── README.md           # This file
```

### Troubleshooting

**Common Issues:**

1. **Build fails**: Check that all dependencies are in `requirements.txt`
2. **API key not working**: Verify the `CEREBRAS_API_KEY` environment variable is set correctly
3. **Application won't start**: Check the start command in Render dashboard
4. **Rate limiting**: The app has built-in rate limiting (5 requests per minute per IP)

**Logs:**

- Check the Render dashboard logs for detailed error information
- Use the `/health` endpoint to verify the application status

### Performance Notes

- The free tier on Render has limitations (sleeps after inactivity)
- Consider upgrading to a paid plan for production use
- The application includes rate limiting to prevent abuse
- Generated UIs are stored in memory (not persistent across restarts)

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test locally
5. Submit a pull request

### License

This project is open source and available under the MIT License.
