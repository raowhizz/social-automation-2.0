# Facebook App Setup Guide

Complete guide to create and configure a Facebook App for multi-tenant OAuth2 social media automation.

---

## Step 1: Create a Facebook Developer Account

1. Go to [Facebook Developers](https://developers.facebook.com/)
2. Click **"Get Started"** in the top right
3. Log in with your Facebook account
4. Complete the registration process
5. Verify your email if required

---

## Step 2: Create a New App

1. Go to [My Apps](https://developers.facebook.com/apps)
2. Click **"Create App"**
3. Select **"Business"** as the app type (for managing Facebook Pages and Instagram)
4. Click **"Next"**

### App Details:
- **App Name**: `Social Automation Multi-Tenant` (or your preferred name)
- **App Contact Email**: Your email address
- **Business Account**: Select existing or create new (optional for development)

5. Click **"Create App"**
6. Complete security check if prompted

---

## Step 3: Add Facebook Login Product

1. In your app dashboard, find **"Add Products"** section
2. Find **"Facebook Login"** and click **"Set Up"**
3. Select **"Web"** as the platform
4. Enter Site URL: `http://localhost:8000` (for development)
5. Click **"Save"** and **"Continue"**

### Configure Facebook Login Settings:

1. Go to **Facebook Login → Settings** (left sidebar)
2. Configure the following:

**Valid OAuth Redirect URIs** (CRITICAL):
```
http://localhost:8000/oauth/facebook/callback
http://localhost:8000/api/v1/oauth/facebook/callback
```

**Settings**:
- Client OAuth Login: **YES**
- Web OAuth Login: **YES**
- Force Web OAuth Reauthentication: **NO**
- Embedded Browser OAuth Login: **NO**
- Use Strict Mode for Redirect URIs: **YES**
- Login from Devices: **NO**

3. Click **"Save Changes"**

---

## Step 4: Add Instagram Graph API Product

1. In app dashboard, find **"Add Products"**
2. Find **"Instagram Graph API"** and click **"Set Up"**
3. No additional configuration needed at this step

---

## Step 5: Configure App Permissions

### Request Required Permissions:

1. Go to **App Review → Permissions and Features** (left sidebar)
2. Request the following permissions:

#### For Facebook Pages:
- **`pages_manage_posts`** - Create, edit, and delete posts on Pages
- **`pages_read_engagement`** - Read engagement data on Pages
- **`pages_show_list`** - Get list of Pages user manages

#### For Instagram:
- **`instagram_basic`** - Access Instagram account info
- **`instagram_content_publish`** - Create Instagram posts

#### For User Info:
- **`email`** - Access user email (usually approved by default)
- **`public_profile`** - Access public profile info (default)

**Note**: Some permissions require App Review. For development/testing, you can use Test Users or add yourself as a developer.

---

## Step 6: Get App Credentials

1. Go to **Settings → Basic** (left sidebar)
2. You'll see:
   - **App ID**: Copy this value
   - **App Secret**: Click **"Show"**, copy this value (keep it secret!)

### Save these values:
```env
FACEBOOK_APP_ID=your_app_id_here
FACEBOOK_APP_SECRET=your_app_secret_here
```

---

## Step 7: Configure App for Development

### Add Test Users (Optional but Recommended):

1. Go to **Roles → Test Users**
2. Click **"Add Test Users"**
3. Create 1-2 test users for testing OAuth flow
4. Test users have full permissions without App Review

### Add Yourself as App Developer:

1. Go to **Roles → Roles**
2. Add yourself or team members as **Developers** or **Administrators**
3. Developers can test all features without App Review approval

---

## Step 8: App Mode Settings

### Development Mode (For Testing):
- App starts in **Development Mode**
- Only developers, testers, and test users can use the app
- All permissions available for testing
- No App Review required

### Live Mode (For Production):
- Switch to **Live Mode** when ready for real users
- Requires App Review for advanced permissions
- Real restaurants can connect their accounts

**For now, stay in Development Mode** - we'll handle App Review later.

---

## Step 9: Configure Data Deletion Callback (Required)

Facebook requires a Data Deletion callback URL:

1. Go to **Settings → Basic**
2. Scroll to **"App Domains"**: Add `localhost` (for development)
3. Scroll to **"Data Deletion Instructions URL"**:
   - Enter: `http://localhost:8000/privacy/data-deletion`
   - Or enter URL to a page explaining data deletion process

---

## Step 10: Platform Settings

1. Go to **Settings → Basic**
2. Click **"+ Add Platform"** at the bottom
3. Select **"Website"**
4. **Site URL**: `http://localhost:8000`
5. Click **"Save Changes"**

---

## Step 11: Testing Setup with Facebook Page

To test posting, you need a Facebook Page:

1. Create a test Facebook Page (if you don't have one):
   - Go to [facebook.com/pages/create](https://www.facebook.com/pages/create)
   - Choose category (e.g., "Restaurant")
   - Name: "Test Restaurant Page"
   - Complete setup

2. Connect Page to Instagram (Optional):
   - Page → Settings → Instagram
   - Connect your Instagram Business account
   - If you don't have Instagram Business, you can test Facebook only first

---

## Step 12: Verify Configuration

Your Facebook App is ready when you have:

- ✅ App ID and App Secret saved
- ✅ Facebook Login configured with redirect URI
- ✅ Instagram Graph API added
- ✅ Permissions requested (or using Test Users)
- ✅ App in Development Mode
- ✅ You're added as App Developer
- ✅ Test Facebook Page created (optional)

---

## Configuration Summary

Copy these to your `.env` file:

```env
# Facebook App Credentials
FACEBOOK_APP_ID=your_app_id_here
FACEBOOK_APP_SECRET=your_app_secret_here

# OAuth Redirect URI (must match Facebook Login settings)
FACEBOOK_OAUTH_REDIRECT_URI=http://localhost:8000/oauth/facebook/callback

# Scopes/Permissions to request
FACEBOOK_OAUTH_SCOPES=email,pages_show_list,pages_read_engagement,pages_manage_posts,instagram_basic,instagram_content_publish
```

---

## For Production (Later)

When ready to deploy:

1. **Update Redirect URIs**:
   - Add production domain: `https://yourdomain.com/oauth/facebook/callback`

2. **App Review**:
   - Submit app for review with required permissions
   - Provide use case documentation
   - Demonstrate the feature using permissions
   - Typical review time: 3-7 days

3. **Switch to Live Mode**:
   - Settings → Basic → App Mode → Switch to Live

4. **Privacy Policy**:
   - Create and host a privacy policy
   - Add URL in Settings → Basic → Privacy Policy URL

5. **Terms of Service**:
   - Create and host terms of service
   - Add URL in Settings → Basic → Terms of Service URL

---

## Troubleshooting

### "Redirect URI Mismatch" Error
- Ensure redirect URI in code **exactly** matches Facebook Login Settings
- Check for trailing slashes, http vs https, port numbers
- URIs are case-sensitive

### "App Not Set Up" Error
- Verify Facebook Login is added and configured
- Check that app is in Development Mode and you're added as developer

### "Permission Denied" Error
- Request permission in App Review → Permissions and Features
- Or use Test Users (they have all permissions)

### Cannot See Instagram Accounts
- Ensure Instagram Graph API is added
- Page must be connected to Instagram Business account
- Not all Instagram accounts can be connected (must be Business)

---

## Next Steps

After completing this setup:
1. ✅ Copy App ID and App Secret to `.env` file
2. ✅ Proceed to Database Setup
3. ✅ Configure environment variables
4. ✅ Start building OAuth flow

---

**Estimated Setup Time**: 15-20 minutes

For questions or issues, refer to:
- [Facebook for Developers Documentation](https://developers.facebook.com/docs/)
- [Facebook Login Documentation](https://developers.facebook.com/docs/facebook-login/)
- [Instagram Graph API Documentation](https://developers.facebook.com/docs/instagram-api/)
