# ClashFish Setup Guide

Complete guide to set up ClashFish AI Coach on your system.

## Prerequisites

- **Python 3.8 or higher**
- **Pip** (Python package manager)
- **Roboflow account** (free tier works)
- **Trained DQN model** (from the original bot training)

## Step 1: Install Python Dependencies

```bash
# Navigate to project directory
cd ClashAnalyzerBot

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install ClashFish dependencies
pip install -r requirements_clashfish.txt
```

## Step 2: Configure Roboflow API

1. **Create Roboflow account:**
   - Visit https://roboflow.com/
   - Sign up for free account

2. **Get API key:**
   - Go to your Roboflow dashboard
   - Click on your profile → Settings
   - Copy your API key

3. **Set up Roboflow models:**
   - You need two trained models:
     - **Card Detection Model**: Detects cards in hand
     - **Troop Detection Model**: Detects troops on field

   - Option 1: Use existing models (if available)
   - Option 2: Train your own models with Clash Royale screenshots

4. **Configure environment:**
   ```bash
   # Create .env file
   cp .env.example .env

   # Edit .env and add your credentials:
   # ROBOFLOW_API_KEY=your_api_key_here
   # WORKSPACE_CARD_DETECTION=your_workspace/card-detection
   # WORKSPACE_TROOP_DETECTION=your_workspace/troop-detection
   ```

## Step 3: Set Up Roboflow Inference Server (Optional)

For local inference without API limits:

```bash
# Install Docker
# Visit: https://docs.docker.com/get-docker/

# Run Roboflow inference server
docker run -d -p 9001:9001 roboflow/roboflow-inference-server-cpu:latest

# Or with GPU support:
docker run -d -p 9001:9001 --gpus all roboflow/roboflow-inference-server-gpu:latest
```

## Step 4: Verify DQN Model

Make sure you have a trained DQN model:

```bash
# Check models directory
ls models/

# You should see files like:
# model_20250603_032527.pth
# model_metadata_20250603_032527.json
```

If you don't have a model:
1. Train the original bot first (see original README)
2. Or download a pre-trained model (if available)

## Step 5: Test Installation

Test that everything works:

```bash
# Test video processor (without Roboflow)
python video_processor.py test_video.mp4

# Test full analysis (requires model)
python clashfish.py analyze test_video.mp4

# Test web server
python api_server.py
# Then visit http://localhost:8000
```

## Step 6: Mobile Setup

### For Web Interface

1. **Start the server:**
   ```bash
   python api_server.py
   ```

2. **Access from phone:**
   - Find your computer's IP address:
     ```bash
     # Linux/Mac
     ifconfig | grep "inet "

     # Windows
     ipconfig
     ```

   - Open browser on phone
   - Navigate to `http://YOUR_IP_ADDRESS:8000`

3. **Upload and analyze:**
   - Record Clash Royale match on phone
   - Upload via web interface
   - View analysis report

### For Local Development

If testing locally (same device):
- Open `frontend/index.html` directly in browser
- Or use a local web server:
  ```bash
  # Python 3
  cd frontend
  python -m http.server 8080

  # Then visit http://localhost:8080
  ```

## Step 7: Production Deployment (Optional)

For hosting ClashFish online:

### Option 1: Heroku
```bash
# Install Heroku CLI
# Create Procfile:
web: uvicorn api_server:app --host 0.0.0.0 --port $PORT

# Deploy:
git add .
git commit -m "Deploy ClashFish"
heroku create your-app-name
git push heroku main
```

### Option 2: AWS/GCP/Azure
- Use EC2/Compute Engine/VM
- Install dependencies
- Run with `uvicorn`
- Set up reverse proxy (nginx)
- Enable HTTPS

### Option 3: Railway/Render
- Connect GitHub repo
- Set environment variables
- Auto-deploy on push

## Troubleshooting

### "No module named 'torch'"
```bash
pip install torch torchvision
```

### "Roboflow API error"
- Check your API key in `.env`
- Verify Roboflow server is running (port 9001)
- Check internet connection

### "No trained model found"
- Make sure `models/` directory exists
- Verify `.pth` files are present
- Train the bot or download a model

### "Video processing failed"
- Check video format (MP4/MOV/AVI)
- Verify OpenCV is installed: `pip install opencv-python`
- Try converting video to MP4 with VLC/ffmpeg

### "Out of memory"
- Reduce FPS: `--fps 1.0` instead of `2.0`
- Process shorter videos
- Close other applications

### Mobile upload not working
- Check firewall settings
- Ensure server is running: `python api_server.py`
- Verify IP address is correct
- Try using `0.0.0.0` as host instead of `localhost`

## Configuration Options

### Video Processing
```python
# In video_processor.py
processor = VideoProcessor(
    fps=2.0,  # Frames per second (higher = more detailed, slower)
    roboflow_workspace_card="your-workspace/card-detection",
    roboflow_workspace_troop="your-workspace/troop-detection",
    roboflow_api_key="your-api-key"
)
```

### Analysis Engine
```python
# In clashfish_engine.py
engine = ClashFishEngine(
    model_path="models/model_latest.pth",
    device="cuda"  # Use "cpu" if no GPU
)
```

### API Server
```python
# In api_server.py
# Change port:
uvicorn.run(app, host="0.0.0.0", port=8000)

# Enable debug mode:
uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
```

## Performance Tips

1. **Use GPU for faster processing:**
   - Install CUDA toolkit
   - Install PyTorch with CUDA: `pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118`
   - Set `device="cuda"` in engine

2. **Reduce video size:**
   - Lower resolution videos process faster
   - Trim videos to just the match (no menus)
   - Use compressed formats (H.264 MP4)

3. **Optimize FPS:**
   - For quick analysis: `fps=1.0`
   - For detailed analysis: `fps=2.0`
   - For very detailed: `fps=3.0` (slow!)

4. **Cache models:**
   - Models are loaded once at startup
   - Keep server running for multiple analyses

## Next Steps

- ✅ Test with sample video
- ✅ Analyze your own games
- ✅ Share reports with friends
- ✅ Join Discord for support
- ✅ Contribute improvements

## Support

Need help?
- Check [CLASHFISH_README.md](CLASHFISH_README.md)
- Open GitHub issue
- Discord community
- Email support

---

**Happy analyzing! May your plays be brilliant! ⚔️**
