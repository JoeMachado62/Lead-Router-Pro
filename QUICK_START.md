# 🚤 Dockside Pro Authentication - Quick Start Guide

Having trouble with setup? This guide will get you running in minutes!

## 🚀 One-Command Setup

From the `/root/Lead-Router-Pro` directory, run:

```bash
python3 quick_setup.py
```

This will:
- ✅ Check Python installation 
- ✅ Create virtual environment
- ✅ Install all dependencies (fixing conflicts)
- ✅ Set up authentication database
- ✅ Create default admin/user accounts

## 🏃‍♂️ Start the Server

### Option 1: Using the start script
```bash
python3 start_server.py
```

### Option 2: Manual start
```bash
# Activate virtual environment
source venv/bin/activate

# Start the server
python main_working_final.py
```

## 🌐 Access Your Application

Once running, visit:
- **Login Page**: http://localhost:8000/login
- **Admin Dashboard**: http://localhost:8000/admin  
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 🔐 Default Login Credentials

**Admin Account:**
- Email: `admin@dockside.life`
- Password: `DocksideAdmin2025!`

**Sample User:**
- Email: `user@dockside.life` 
- Password: `DocksideUser2025!`

⚠️ **Change these passwords immediately after first login!**

## 🧪 Test the System

In another terminal:
```bash
cd /root/Lead-Router-Pro
source venv/bin/activate
python test_auth_system.py
```

## 🔧 Common Issues & Solutions

### "Command 'python' not found"
- Use `python3` instead of `python`
- Or install: `apt install python-is-python3`

### "pip install conflicts" 
- The `quick_setup.py` script fixes this automatically
- Or manually: `pip install -r requirements.txt`

### "Connection refused" when testing
- Make sure the server is running first
- Check if port 8000 is free: `netstat -tlnp | grep 8000`

### "Module not found" errors
- Activate virtual environment: `source venv/bin/activate`
- Reinstall dependencies: `pip install -r requirements.txt`

## 📧 Enable Email (Optional)

For 2FA emails, edit `.env`:
```env
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

For Gmail:
1. Enable 2FA on Google account
2. Generate App Password
3. Use App Password as `SMTP_PASSWORD`

## 🎯 What You Get

✅ **Secure Login**: Email + password + 2FA codes
✅ **Professional UI**: Clean login page with smooth flow  
✅ **Multi-tenant**: Ready for multiple domains/companies
✅ **Admin Protection**: Dashboard requires authentication
✅ **API Security**: JWT tokens with refresh capability
✅ **Audit Logging**: All security events tracked
✅ **Account Safety**: Lockout protection, session timeout

## 🆘 Still Having Issues?

1. **Check Python version**: `python3 --version` (should be 3.8+)
2. **Check virtual environment**: `which python` (should point to venv)
3. **Check dependencies**: `pip list | grep fastapi`
4. **Check logs**: Look for error messages when starting server
5. **Check ports**: Make sure 8000 is available

## 🎉 Success!

When everything works:
- ✅ Server starts without errors
- ✅ Login page loads at http://localhost:8000/login
- ✅ You can log in with default credentials  
- ✅ Admin dashboard redirects to login when not authenticated
- ✅ Test script passes all checks

**Your secure multi-tenant authentication system is ready!** 🚀

---

## 📝 Next Steps

1. Change default passwords
2. Configure email for 2FA
3. Customize branding/styling
4. Add more users via admin interface
5. Deploy to production with HTTPS

Need the full documentation? See `AUTHENTICATION_SETUP.md`
