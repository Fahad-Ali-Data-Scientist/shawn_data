# Enable Camera on HTTP Server

## 🚀 EASIEST METHOD - Auto Start Script

### Windows:
```bash
start_with_camera.bat
```

### Linux/Mac:
```bash
./start_with_camera.sh
```

**This script automatically:**
- Starts Flask server
- Gets your server IP
- Opens Chrome with camera enabled
- Shows access URLs

---

## 📱 Manual Setup for Each Browser

### Chrome/Edge (Windows)

**Step 1:** Find your server IP
```bash
ipconfig
```

**Step 2:** Close ALL Chrome windows

**Step 3:** Run this command (replace YOUR_IP):
```bash
chrome --unsafely-treat-insecure-origin-as-secure="http://192.168.1.100:5000" --user-data-dir=C:\temp\chrome
```

**Step 4:** Open `http://192.168.1.100:5000`

---

### Chrome (Linux/Mac)

```bash
google-chrome --unsafely-treat-insecure-origin-as-secure="http://YOUR_IP:5000" --user-data-dir=/tmp/chrome
```

---

### Firefox

1. Type: `about:config`
2. Search: `media.devices.insecure.enabled`
3. Set to: **true**
4. Search: `media.getusermedia.insecure.enabled`
5. Set to: **true**
6. Restart Firefox

---

## 📱 Mobile Access

### Android Chrome
1. Connect phone via USB
2. On PC: `chrome://inspect`
3. Enable port forwarding: `5000 -> localhost:5000`
4. On phone: Open `localhost:5000`

### iOS
Requires HTTPS (no workaround)
Use video upload feature instead

---

## ⚠️ Important Notes

1. **Development only** - Don't use in production
2. **Reset after testing** - Remove browser flags
3. **For production** - Use proper HTTPS
4. **Video upload** works without any setup

---

## 🎯 Summary

| Access Method | Camera Works? | Setup Needed? |
|---------------|---------------|---------------|
| localhost | ✅ Yes | ❌ No |
| HTTP + IP | ✅ Yes | ✅ Browser flag |
| HTTPS | ✅ Yes | ❌ No |

---

**See `ENABLE_CAMERA_HTTP.txt` for detailed instructions**

