# DockSide Pros Lead Router - Setup Guide

## 🎯 MVP Implementation Complete!

This guide will help you deploy and configure the DockSide Pros Lead Router MVP for automatic lead assignment.

## 📋 What's Included

### Core Components
- **`lead_router.py`** - Main lead routing logic with vendor matching
- **`webhook_server.py`** - Flask web server to handle Elementor webhooks
- **`config.py`** - Configuration management
- **`test_system.py`** - Comprehensive system testing
- **`ghl_field_creator.py`** - Custom field creation (already working)
- **`ghl_field_key_retriever.py`** - Field mapping utilities

### Deployment Files
- **`requirements.txt`** - Python dependencies
- **`deploy.sh`** - Automated VPS deployment script
- **`.env.example`** - Environment configuration template

## 🚀 Quick Start (Development)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your actual GHL credentials
```

### 3. Test the System
```bash
python test_system.py
```

### 4. Start the Webhook Server
```bash
python webhook_server.py
```

### 5. Test Webhook Endpoint
```bash
curl -X POST http://localhost:3000/webhook/test
```

## 🏗️ Production Deployment

### Option 1: Automated VPS Deployment
```bash
# On your VPS (Ubuntu/Debian)
sudo chmod +x deploy.sh
sudo ./deploy.sh
```

### Option 2: Manual Setup
1. **Install Python 3.8+**
2. **Create virtual environment**
3. **Install dependencies**
4. **Configure nginx reverse proxy**
5. **Set up systemd service**
6. **Configure SSL certificate**

## ⚙️ Configuration Steps

### 1. GoHighLevel Setup

#### A. Get Pipeline and Stage IDs
1. Go to your GHL account → Settings → Pipelines
2. Find your marine services pipeline
3. Copy the pipeline ID and stage IDs
4. Update `.env` file:
```env
PIPELINE_ID=your_actual_pipeline_id
NEW_LEAD_STAGE_ID=your_new_lead_stage_id
```

#### B. Verify Custom Fields
Your custom fields are already created! The system uses:

**For Leads (Clients):**
- `specific_service_needed`
- `zip_code_of_service`
- `service_category`
- `vessel_make`, `vessel_model`, `vessel_year`
- `special_requests__notes`

**For Vendors:**
- `services_provided`
- `service_zip_codes`
- `taking_new_work`
- `ghl_user_id`
- `last_lead_assigned`
- `vendor_company_name`

#### C. Set Up Vendor Contacts
For each vendor in GHL, ensure these fields are populated:
```
Services Provided: "Boat Maintenance, Engines and Generators"
Service Zip Codes: "33101, 33102, 33103"
Taking New Work?: "Yes"
GHL User ID: "user_id_from_ghl"
```

### 2. Elementor Forms Setup

#### A. Add Webhook to Forms
1. Edit your Elementor form
2. Go to Actions After Submit
3. Add "Webhook" action
4. Set webhook URL: `https://your-domain.com/webhook/elementor`

#### B. Form Field Mapping
Ensure your forms have these field names (or similar):
- `name` or `full_name`
- `email` or `email_address`
- `phone` or `phone_number`
- `service` or `service_type`
- `zip_code` or `postal_code`
- `message` or `special_requests`

#### C. Form Source Identification
Set form names to help with service classification:
- `boat-detailing`
- `engine-repair`
- `yacht-welding`
- `ac-repair`
- etc.

## 🧪 Testing Checklist

### Pre-Deployment Tests
- [ ] GHL API connection works
- [ ] Vendor detection finds your vendors
- [ ] Service classification works correctly
- [ ] Lead processing creates contacts
- [ ] Webhook server responds to requests

### Post-Deployment Tests
- [ ] Webhook URL is accessible from internet
- [ ] SSL certificate is working
- [ ] Form submissions create leads in GHL
- [ ] Leads are assigned to correct vendors
- [ ] Vendor assignment timestamps update

## 🔧 Troubleshooting

### Common Issues

#### 1. "No vendors found"
**Cause:** Vendor contacts missing required fields
**Solution:** 
- Check vendor contacts have `services_provided` field
- Ensure `taking_new_work` is set to "Yes"
- Verify `service_zip_codes` are populated

#### 2. "Service type not classified"
**Cause:** Form data doesn't match service mappings
**Solution:**
- Check form field names match expected values
- Add custom mappings in `lead_router.py`
- Verify form source names

#### 3. "Failed to create contact"
**Cause:** GHL API issues or missing required fields
**Solution:**
- Check GHL API credentials
- Verify required fields (name, email) are present
- Check GHL API rate limits

#### 4. "Webhook not receiving data"
**Cause:** Network/firewall issues
**Solution:**
- Check server is running on correct port
- Verify firewall allows incoming connections
- Test with curl or Postman

### Debug Commands
```bash
# Check service status
systemctl status lead-router

# View logs
tail -f /var/log/lead-router/webhook.log

# Test webhook locally
python test_system.py

# Check nginx configuration
nginx -t

# Restart services
systemctl restart lead-router nginx
```

## 📊 Monitoring & Maintenance

### Key Metrics to Monitor
- Lead processing success rate
- Vendor assignment distribution
- Response times
- Error rates

### Regular Maintenance
- Monitor vendor "taking new work" status
- Update service mappings as needed
- Review and clean up test leads
- Check system logs for errors

## 🔄 Next Steps (Future Enhancements)

### Phase 2 Improvements
- [ ] Vendor performance scoring
- [ ] Advanced service classification (AI)
- [ ] Customer feedback integration
- [ ] Analytics dashboard
- [ ] Mobile notifications for vendors

### Scaling Considerations
- [ ] Database for lead history
- [ ] Redis for caching
- [ ] Load balancing for high traffic
- [ ] Automated vendor onboarding

## 📞 Support

### System Architecture
```
WordPress/Elementor → Webhook → Lead Router → GoHighLevel
                                     ↓
                              Vendor Assignment
                                     ↓
                              Opportunity Creation
```

### Key Files for Customization
- **Service Mappings:** `lead_router.py` → `_load_service_mappings()`
- **Vendor Logic:** `lead_router.py` → `find_matching_vendors()`
- **Form Processing:** `webhook_server.py` → `extract_form_data()`

## ✅ Success Criteria

Your MVP is successful when:
- [ ] 90% of form submissions are properly routed
- [ ] Lead assignment happens within 30 seconds
- [ ] Vendors receive leads fairly distributed
- [ ] Zero manual lead routing required
- [ ] System runs reliably 24/7

## 🎉 Congratulations!

You now have a fully functional lead routing system that will:
1. **Automatically receive** leads from Elementor forms
2. **Classify service types** based on form data
3. **Match vendors** by service and location
4. **Assign leads fairly** using round-robin
5. **Create contacts and opportunities** in GoHighLevel
6. **Track assignment history** for reporting

The system is ready for production use and will significantly reduce manual lead routing work while ensuring fair distribution to your vendor network.
