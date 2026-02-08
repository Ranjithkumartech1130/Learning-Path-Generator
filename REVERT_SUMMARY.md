# ↩️ Reverted: Returned to Dark Theme

## 🛠️ Changes Reverted

As requested, I have reverted the changes from the previous prompt.

### 1. **Dark Theme Restored** 🌑
The application is back to its original "wonderful" dark theme:
- Deep dark blue/black backgrounds (`#030712`)
- Vibrant glowing accents (`#6366f1`)
- Dark glassmorphism cards
- White text on dark backgrounds

### 2. **Scroll Behavior Restored** 🔄
- **Bidirectional Parallax**: You can now scroll back up to see the landing page again.
- Removed the "one-way" scroll lock.
- kept `autoAlpha: 0` improvement from the fix before that (Step 173) to ensuring proper click-through handling, but allowed it to reverse.

## ✅ Current Status
- **Style**: Dark Mode (Original)
- **Behavior**: Scroll down to enter, scroll up to see landing page.
- **Back to Top**: The button works to scroll you back up smoothly.
- **Server**: Restarted and running on http://localhost:5000.

## 🚀 How to Verify
1. **Refresh** the page.
2. Confirm the **Dark Mode** is back.
3. Scroll down, then scroll back up -> You should see the **Cloud/Mountain scene reappear**.
