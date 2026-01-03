# Instagram Posting Setup Guide

## Status: ✅ OAuth Scopes Configured

### What Was Done (Automated):
1. ✅ Updated `.env` file with Instagram OAuth scopes:
   - `instagram_basic` - Access Instagram account info
   - `instagram_content_publish` - Create Instagram posts
   - `instagram_manage_insights` - Fetch analytics
2. ✅ Server restarted with new configuration
3. ✅ Restaurant Config page opened for reconnection

---

## Next Steps (Manual - YOU NEED TO DO):

### Step 1: Verify Facebook App Permissions
**Time**: 2 minutes

1. Go to: https://developers.facebook.com/apps/696564846846384/app-review/permissions/
2. Check that these permissions show "In Development":
   - `instagram_basic`
   - `instagram_content_publish`  
   - `instagram_manage_insights`
3. If not visible, they're automatically available in Development Mode

### Step 2: Connect Instagram Business Account to Facebook Page
**Time**: 3-5 minutes

**Option A: If you have Instagram Business Account**
1. Go to your Facebook Page
2. Settings → Instagram
3. Click "Connect Account"
4. Login to your Instagram Business account

**Option B: If you have Personal Instagram Account**
1. Open Instagram app
2. Go to: Profile → Menu (☰) → Settings
3. Account → Switch to Professional Account
4. Choose "Business"
5. Complete setup
6. Then follow Option A above

### Step 3: Reconnect OAuth in Restaurant Config
**Time**: 2 minutes

The page should be open in your browser at:
https://kristian-unrenewable-mercedez.ngrok-free.dev/ui/config

1. Scroll to "Connected Social Accounts" section
2. Click "🗑️ Disconnect" on existing Facebook connection
3. Click "📘 Connect Facebook Account"
4. Complete Facebook OAuth flow
5. **IMPORTANT**: You should now see TWO accounts:
   - 📘 Facebook Page (e.g., "Krusty Pizza & Pasta")
   - 📷 Instagram Business Account (e.g., "@krusty_pizza")

### Step 4: Test Instagram Posting
**Time**: 3 minutes

1. Go to: https://kristian-unrenewable-mercedez.ngrok-free.dev/ui/create
2. In "Platform" dropdown, select: **Instagram**
3. Upload a square image (1080×1080 recommended)
4. Write caption: "Testing Instagram posting! 🍕✨ #test #pizza"
5. Click "Post Now"
6. **Check Instagram** - post should appear within 30 seconds

---

## Troubleshooting:

### Issue: Instagram account not showing after OAuth
**Solution**:
- Make sure Instagram is a Business account
- Verify it's connected to the Facebook Page
- Disconnect and reconnect in Facebook Page settings

### Issue: "Permission denied" error when posting
**Solution**:
- Check that `instagram_content_publish` is in Development mode
- Re-run OAuth flow to get fresh token with new permissions

### Issue: Post creation fails
**Solution**:
- Ensure image is publicly accessible (ngrok URL works)
- Check image size < 8MB
- Verify caption < 2,200 characters
- Max 30 hashtags

---

## Configuration Summary:

### OAuth Scopes (Updated):
```env
FACEBOOK_OAUTH_SCOPES=pages_show_list,pages_read_engagement,pages_manage_posts,pages_read_user_content,instagram_basic,instagram_content_publish,instagram_manage_insights
```

### What This Enables:
- ✅ Instagram Business account detection during OAuth
- ✅ Instagram post creation (images + captions)
- ✅ Instagram analytics fetching
- ✅ Scheduled Instagram posts
- ✅ Calendar generation for Instagram

### Current Limitation:
- ⚠️ Development Mode only - works for:
  - Your own accounts
  - Accounts of people you add as "Testers"
- ⚠️ For production (any restaurant): Need Facebook App Review

---

## Next Phase (After Testing):

Once Instagram posting works:
1. Test all features (manual post, scheduled post, calendar)
2. Add validation (image size, caption length, hashtags)
3. Polish UI/UX
4. Prepare for Facebook App Review
5. Switch to Live Mode for production

---

**Date**: 2026-01-02  
**Version**: 2.2.0  
**Status**: Ready for testing with Development Mode accounts
