# HTTPS Setup for Camera Access

## 🚀 Quick Setup (Recommended - ngrok)

### Step 1: Install ngrok (One-time)

**Linux/Ubuntu:**
```bash
# Download and install
wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz
tar xvzf ngrok-v3-stable-linux-amd64.tgz
sudo mv ngrok /usr/local/bin/
```

**macOS:**
```bash
brew install ngrok/ngrok/ngrok
```

**Windows:**
1. Download from: https://ngrok.com/download
2. Extract `ngrok.exe`
3. Move to `C:\Windows\System32\`

### Step 2: Setup ngrok Authentication (One-time)

```bash
# 1. Sign up (free): https://dashboard.ngrok.com/signup
# 2. Get your authtoken from dashboard
# 3. Run:
ngrok config add-authtoken YOUR_AUTH_TOKEN
```

### Step 3: Run with HTTPS

**Linux/Mac:**
```bash
./setup_https_ngrok.sh
```

**Windows:**
```bash
setup_https_ngrok.bat
```

**Done!** You'll get a URL like: `https://abc123.ngrok.io`

---

## 📱 For Clients (Users)

Clients just need to:
1. Open the HTTPS URL you provide
2. Click "Live Camera Detection"
3. Allow camera permissions
4. **That's it!** No browser setup needed!

---

## 🔧 Manual ngrok Setup

If scripts don't work, run manually:

### Start Flask:
```bash
python app.py
```

### In another terminal, start ngrok:
```bash
ngrok http 5000
```

You'll see:
```
Forwarding  https://abc123.ngrok.io -> http://localhost:5000
```

Share the HTTPS URL with clients!

---

## 🌐 Alternative: Use cloudflared (No signup required)

### Install cloudflared:

**Linux:**
```bash
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64
sudo mv cloudflared-linux-amd64 /usr/local/bin/cloudflared
sudo chmod +x /usr/local/bin/cloudflared
```

**Mac:**
```bash
brew install cloudflared
```

### Run:
```bash
# Start Flask
python app.py

# In another terminal
cloudflared tunnel --url http://localhost:5000
```

You'll get a URL like: `https://xyz.trycloudflare.com`

**No signup needed!**

---

## 🏢 Production Setup (Your Own Domain)

### Option 1: Let's Encrypt (Free SSL)

Install certbot:
```bash
# Ubuntu/Debian
sudo apt install certbot python3-certbot-nginx

# Generate certificate (replace your-domain.com)
sudo certbot certonly --standalone -d your-domain.com
```

Update `app.py` to use SSL:
```python
if __name__ == "__main__":
    socketio.run(
        app,
        host="0.0.0.0",
        port=5000,
        debug=True,
        ssl_context=(
            '/etc/letsencrypt/live/your-domain.com/fullchain.pem',
            '/etc/letsencrypt/live/your-domain.com/privkey.pem'
        )
    )
```

### Option 2: Self-Signed Certificate (Testing)

```bash
# Generate certificate
openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365

# Update app.py
ssl_context=('cert.pem', 'key.pem')
```

---

## 📊 Comparison

| Method | Pros | Cons | Best For |
|--------|------|------|----------|
| **ngrok** | ✅ Easy, Fast setup<br>✅ HTTPS ready<br>✅ Public URL | ⚠️ Requires signup<br>⚠️ Free tier limits | Testing, Demos |
| **cloudflared** | ✅ No signup<br>✅ Fast setup<br>✅ Free unlimited | ⚠️ Random URLs | Quick testing |
| **Let's Encrypt** | ✅ Free forever<br>✅ Your domain<br>✅ Production ready | ⚠️ Need domain<br>⚠️ More setup | Production |
| **Self-signed** | ✅ No external service<br>✅ Complete control | ⚠️ Browser warnings<br>⚠️ Not for production | Local testing |

---

## 🎯 Recommended Workflow

**For Testing/Development:**
```bash
./setup_https_ngrok.sh
```
Share the URL with your team!

**For Production:**
- Get a domain name
- Use Let's Encrypt
- Deploy on cloud (AWS/Azure/DigitalOcean)

---

## ⚡ Quick Commands

### Start with ngrok:
```bash
# Terminal 1
python app.py

# Terminal 2
ngrok http 5000
```

### Start with cloudflared:
```bash
# Terminal 1
python app.py

# Terminal 2
cloudflared tunnel --url http://localhost:5000
```

---

## 🔒 Security Note

- ngrok/cloudflared: Fine for development/testing
- Production: Use proper SSL with your domain
- Never share authtoken or credentials

---

## ✅ What Clients Need

**Nothing!** 

Just send them the HTTPS URL:
- No browser configuration
- No command line
- No technical knowledge
- Just open link and allow camera

**That's the whole point of HTTPS setup!** 🎉

