# Resume Template Selector - Implementation Guide

## ✅ What's Been Done:

1. **Added LinkedIn & Phone Fields** to Profile Setup (index.html)
   - LinkedIn Profile URL input field
   - Mobile Number input field
   
2. **Updated JavaScript** to save LinkedIn & Phone (script.js)
   - Modified `saveProfile()` function to include these fields

3. **Created Template Styles** (template-styles.css)
   - 5 beautiful resume templates with different color schemes
   - Modern Professional (Dark + Gold)
   - Creative Orange (Orange + Dark)
   - Elegant Burgundy (Burgundy + Gold)
   - Tech Professional (Navy + Blue)
   - Coral Classic (Coral + Teal)

4. **Created Template Selector JavaScript** (template-selector.js)
   - Function to select templates
   - Updates active state visually

## 📝 Manual Steps Required:

### Step 1: Add Template Styles to index.html
Add this line in the `<head>` section of `index.html` (around line 16):
```html
<link rel="stylesheet" href="template-styles.css">
```

### Step 2: Add Template Selector Script
Add this line before the closing `</body>` tag in `index.html` (around line 373):
```html
<script src="template-selector.js"></script>
```

### Step 3: Replace Resume Tab Content
In `index.html`, find the Resume tab section (around line 332-345) and replace it with the content from:
`TEMPLATE_SELECTOR_HTML.html`

### Step 4: Update buildPremiumResume Function
In `script.js`, find the `buildPremiumResume` function (around line 279) and make these changes:

1. Add at the beginning of the function (after line 282):
```javascript
// Use actual user data for contact info
const phone = data.contact.phone || currentUser.profile?.phone || "+1 (555) 123-4567";
const linkedin = data.contact.linkedin || currentUser.profile?.linkedin || "linkedin.com/in/user";
```

2. Change the phone line (around line 327):
```javascript
<div class="contact-item"><i data-lucide="phone"></i> ${phone}</div>
```

3. Change the LinkedIn line (around line 330):
```javascript
<div class="contact-item"><i data-lucide="linkedin"></i> ${linkedin}</div>
```

4. Add template class to the resume div (around line 320):
Change:
```javascript
<div class="premium-resume">
```
To:
```javascript
<div class="premium-resume resume-${window.selectedTemplate || 'coral'}">
```

### Step 5: Update AI Backend
The AI backend (`ai/main.py`) has already been updated to:
- Accept LinkedIn and phone from the request
- Use them in the resume generation

## 🎨 How It Works:

1. **User fills profile** with LinkedIn & Phone
2. **User selects a template** from 5 beautiful options
3. **Clicks "Generate AI Resume"**
4. **AI creates resume** with:
   - All user details (email, LinkedIn, phone, bio, skills, etc.)
   - Selected template color scheme
   - Personalized learning roadmap
5. **User downloads** as PDF

## 🚀 Testing:

1. Register/Login
2. Fill profile including LinkedIn & Phone
3. Go to AI Resume tab
4. Select a template (try different ones!)
5. Generate resume
6. Download as PDF

## 📁 Files Created/Modified:

- ✅ `index.html` - Added LinkedIn & Phone fields
- ✅ `script.js` - Updated to save LinkedIn & Phone
- ✅ `template-styles.css` - NEW: Template color schemes
- ✅ `template-selector.js` - NEW: Template selection logic
- ✅ `TEMPLATE_SELECTOR_HTML.html` - NEW: HTML for template selector
- ✅ `ai/main.py` - Updated to use LinkedIn & Phone data

All files are ready in: `s:\Learning-path-generator\backend\public\`
