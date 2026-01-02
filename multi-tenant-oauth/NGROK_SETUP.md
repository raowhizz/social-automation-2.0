# ngrok Setup for Image Hosting

## Overview
ngrok has been configured to expose localhost:8000 to the internet, allowing Facebook and Instagram to access uploaded images.

## Configuration Details

### ngrok Tunnel
- **Public URL**: https://kristian-unrenewable-mercedez.ngrok-free.dev
- **Local Port**: 8000
- **Status**: Running
- **Tunnel Type**: HTTPS

### Environment Variables Updated
The following variables in `.env` have been updated to use the ngrok URL:

```bash
API_URL=https://kristian-unrenewable-mercedez.ngrok-free.dev
PUBLIC_URL=https://kristian-unrenewable-mercedez.ngrok-free.dev
```

### Image URLs
All images uploaded to the brand asset library will now have URLs like:
```
https://kristian-unrenewable-mercedez.ngrok-free.dev/uploads/images/{filename}
```

These URLs are publicly accessible and can be fetched by Facebook/Instagram when posting.

## Testing Image Posting

To test that images now work in posts:

1. Go to the posting UI: http://localhost:8000/ui
2. Select an image from your brand asset library
3. Create a post with the image
4. The image should now appear in your Facebook/Instagram post

## Important Notes

### For Development (Current Setup)
- ngrok tunnel is active and running in the background
- Each time you restart ngrok, the URL will change (on free tier)
- You'll need to update `.env` with the new URL and restart the server

### For Production
- **Replace ngrok with AWS S3** for permanent, scalable image hosting
- S3 provides:
  - Permanent URLs that don't change
  - Better performance and CDN support
  - No tunnel maintenance required
  - Professional solution

## How to Keep ngrok Running

The ngrok tunnel is currently running as background process ID: 7e5505

To check ngrok status:
```bash
# View ngrok web interface (shows request logs)
open http://localhost:4040
```

To restart ngrok if needed:
```bash
# Kill current ngrok process
pkill ngrok

# Start new tunnel
ngrok http 8000 --log=stdout &

# Get new URL from logs and update .env
# Then restart FastAPI server
```

## Next Steps

1. **Test image posting** with the current setup
2. **For production deployment**: Set up AWS S3 for permanent image hosting
3. **Update .env** with S3 configuration when ready:
   ```bash
   # S3 Configuration (for production)
   AWS_ACCESS_KEY_ID=your_access_key
   AWS_SECRET_ACCESS_KEY=your_secret_key
   AWS_S3_BUCKET=your-bucket-name
   AWS_S3_REGION=us-east-1
   API_URL=https://your-bucket.s3.amazonaws.com
   ```

## Troubleshooting

### ngrok URL changed
If the ngrok URL changes after restart:
1. Update `API_URL` and `PUBLIC_URL` in `.env`
2. Restart FastAPI: `pkill uvicorn && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &`

### Images still not showing
1. Check ngrok is running: `ps aux | grep ngrok`
2. Verify API_URL in .env matches ngrok URL
3. Check server restarted after .env change
4. View ngrok requests at http://localhost:4040

## Status: ✅ READY FOR TESTING

ngrok tunnel is active and image URLs are now publicly accessible for Facebook/Instagram posting!
