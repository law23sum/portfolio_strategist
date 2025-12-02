# Debugging 403 Permission Denied Errors

## Overview

This guide helps diagnose and fix 403 "Permission denied" errors in the iOS app. The app now includes enhanced error logging and a debug screen to help identify the root cause.

## Quick Debugging Steps

### Step 1: Check the Debug Screen

1. Open the iOS app
2. Navigate to **Profile** tab
3. Scroll down to **Settings** section
4. Tap **Debug Info**
5. Review the debug information:
   - **API Base URL**: Should match your Django server
   - **Has Access Token**: Should be "Yes" if logged in
   - **Has Refresh Token**: Should be "Yes" if logged in
   - **Token Valid**: Should be "Yes" for valid tokens
   - **User Email/ID**: Should show your account info

### Step 2: Check Console Logs

When a 403 error occurs, the app now logs detailed information:

**In Metro Bundler Terminal:**
```
[API] 403 Forbidden - Permission denied
[API] Request URL: http://127.0.0.1:8000/api/endpoint/
[API] Request Method: GET
[API] Has Token: true
[API] Token Preview: eyJ0eXAiOiJKV1QiLCJh...
[API] 403 Response Body: {"detail": "You do not have permission..."}
[API] 403 Response Headers:
[API]   content-type: application/json
[API]   ...
```

**What to look for:**
- The exact URL that failed
- Whether a token was present
- The error message from Django
- Response headers

### Step 3: Check Django Server Logs

**In your Django terminal (where `python manage.py runserver` is running):**

Look for the exact 403 error message. Django REST Framework will log:
- The view that was accessed
- The permission class that denied access
- The user making the request
- The reason for denial

Example Django log:
```
WARNING: Permission denied for user: username@example.com
View: RecordsExplorerView
Permission: IsAuthenticated
Reason: User account is inactive
```

## Common Causes and Solutions

### 1. Token Expired or Invalid

**Symptoms:**
- Debug screen shows "Token Valid: No"
- Token Error message present
- 403 occurs even after login

**Solution:**
1. Log out and log back in
2. Check if token refresh is working (app should auto-refresh)
3. Verify Django `SIMPLE_JWT` settings in `settings.py`:
   ```python
   SIMPLE_JWT = {
       "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
       "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
       ...
   }
   ```

### 2. Wrong API Base URL

**Symptoms:**
- Debug screen shows incorrect API Base URL
- Network errors or connection refused
- 403 errors on all endpoints

**Solution:**
1. Check `src/config/api.ts`:
   ```typescript
   const IOS_SIMULATOR_HOST = 'http://127.0.0.1:8000';
   const DEFAULT_LAN_HOST = 'http://192.168.0.100:8000';
   ```
2. For iOS Simulator: Use `http://127.0.0.1:8000` or `http://localhost:8000`
3. For physical device: Use your Mac's IP address (find with `ifconfig | grep "inet "`)
4. Update `Info.plist` to allow your IP address (see below)

### 3. User Account Issues

**Symptoms:**
- Token is valid but 403 persists
- Django logs show "User account is inactive" or similar

**Solution:**
1. Check Django admin: `/admin/users/customuser/`
2. Verify user account is active
3. Check if user has required permissions
4. Try logging in with a different account

### 4. CORS or Network Configuration

**Symptoms:**
- 403 on all requests
- Network errors
- Connection refused

**Solution:**
1. **Update Info.plist** (`ios/mobile/Info.plist`):
   ```xml
   <key>NSExceptionDomains</key>
   <dict>
       <key>YOUR_IP_ADDRESS</key>
       <dict>
           <key>NSExceptionAllowsInsecureHTTPLoads</key>
           <true/>
       </dict>
   </dict>
   ```

2. **Check Django CORS settings** (`portfolio_strategist/settings.py`):
   ```python
   CORS_ALLOWED_ORIGINS = [
       "http://localhost:8000",
       "http://127.0.0.1:8000",
       "http://YOUR_IP:8000",
   ]
   ```

3. **Verify Django server is running**:
   ```bash
   python manage.py runserver 0.0.0.0:8000
   ```
   Note: Use `0.0.0.0` to allow connections from other devices

### 5. Endpoint-Specific Permissions

**Symptoms:**
- 403 on specific endpoints only
- Other endpoints work fine

**Solution:**
1. Check the view's `permission_classes` in Django
2. Some views may require:
   - `IsAdminUser` (admin only)
   - `IsAuthenticated` (logged in users)
   - Custom permissions
3. Check Django logs for the specific permission class that denied access

## Enhanced Error Messages

The app now provides more detailed error messages:

**Before:**
```
Permission denied
```

**After:**
```
Permission denied. The server explicitly denied access to this resource. 
Please check:
1. Django server logs for the exact permission error
2. Your user account has the required permissions
3. The API endpoint URL is correct
4. Try logging out and logging back in
```

## Debugging Checklist

When you encounter a 403 error:

- [ ] Check Debug Info screen in Profile tab
- [ ] Review Metro bundler console logs
- [ ] Check Django server terminal logs
- [ ] Verify API Base URL is correct
- [ ] Confirm token exists and is valid
- [ ] Try logging out and back in
- [ ] Check user account status in Django admin
- [ ] Verify CORS settings
- [ ] Check Info.plist network exceptions
- [ ] Test with a different user account
- [ ] Verify Django server is accessible from device/simulator

## Getting Help

If you're still stuck:

1. **Copy Debug Info**: Tap "Copy to Console" in Debug Info screen
2. **Check Metro Logs**: Look for `[API]` prefixed messages
3. **Check Django Logs**: Look for permission denial messages
4. **Share Information**:
   - Debug Info screen contents
   - Relevant console logs
   - Django server logs
   - The endpoint that's failing
   - Steps to reproduce

## Testing Token Refresh

The app automatically refreshes tokens on 403 errors. To test:

1. Wait for access token to expire (default: 60 minutes)
2. Make an API request
3. Check logs - you should see:
   ```
   [API] Token present but 403 received - token may be invalid or expired
   [API] Attempting token refresh...
   [API] Token refresh successful, retrying request...
   ```

If token refresh fails, you'll need to log in again.

