# Deploying Desk Five publicly (free, private code)

This puts your app on a real public URL anyone can click — including
on LinkedIn — while keeping your code in a **private** GitHub repo.

You'll use **GitHub** (to store the code) + **Render** (to run it,
free tier). Both have visual dashboards, no terminal commands needed
for the deploy itself.

---

## Part A — Put the code on GitHub (private)

1. Go to https://github.com and log in (or sign up if you don't have
   an account)
2. Click the **+** icon top-right → **New repository**
3. Name it something like `desk-five-ai-advisor`
4. Set visibility to **Private** (important — this keeps your code
   hidden even though the live site will be public)
5. Click **Create repository**
6. On the next page, click **uploading an existing file** (a blue
   link near the top)
7. Drag in your whole `stock-advisor` folder contents — `backend/`,
   `frontend/`, `README.md` — or zip and drag the zip, GitHub will
   accept either
8. **Do NOT upload your `.env` file** — that has your real API key in
   it. Only `.env.example` (the template, no real key) should go up.
   If you're not sure, check the file list before committing.
9. Scroll down, click **Commit changes**

Your code is now stored on GitHub, visible only to you.

## Part B — Deploy it on Render

1. Go to https://render.com → **Get Started** → sign up using
   **"Sign up with GitHub"** (this links the two automatically, no
   extra passwords)
2. Once logged in, click **New +** (top right) → **Web Service**
3. Render will show your GitHub repos — find `desk-five-ai-advisor`
   and click **Connect**
   - If it doesn't appear, click **Configure account** and grant
     Render access to that private repo
4. Fill in the settings Render asks for:
   - **Name**: anything, e.g. `desk-five-advisor` (this becomes part
     of your URL)
   - **Root Directory**: `backend`  ← important, since your Flask
     app lives inside the `backend` folder, not the repo root
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Instance Type**: **Free**
5. Scroll to **Environment Variables** → click **Add Environment
   Variable**:
   - Key: `GROQ_API_KEY`
   - Value: paste your real Groq key here

   This is the *correct* place for your key when going public — it's
   stored securely by Render, never visible in your code or repo.
6. Click **Create Web Service**

Render will now build and start your app — you'll see live logs.
First deploy usually takes 2-4 minutes. When it says **"Live"** at
the top, you're done.

## Part C — Get your public link

Render gives you a URL like:

```
https://desk-five-advisor.onrender.com
```

That's your live, public link. Test it yourself first — click
through a couple of stocks to confirm it works before sharing it
anywhere.

---

## What to expect on the free tier

- The app **sleeps** after 15 minutes with no visitors
- The **first** click after it's been sleeping takes ~30-50 seconds to
  "wake up" — this is normal, not broken. Anyone after that gets fast
  responses for a while
- If you start getting real traffic from your LinkedIn post and want
  it always-fast, Render's paid tier removes the sleep — but no need
  to pay anything to start

## Before you post on LinkedIn

- [ ] Test the live link yourself end-to-end (pick a stock, run
      analysis, confirm you get a real BUY/HOLD/SELL report)
- [ ] Set a spending limit/alert on your Groq account
      (console.groq.com → Billing), just in case the post gets more
      traffic than expected
- [ ] Add the "not investment advice" disclaimer to your LinkedIn post
      text too, not just the page footer
- [ ] Consider mentioning in the post what it actually demonstrates —
      e.g. "live data pipeline (pandas/yfinance) + LLM-based reasoning
      layer (Groq) + Flask API" — recruiters skim, so naming the
      concrete skills helps more than just "I built an AI app"

## Updating the app later

Whenever you change code locally, you'll re-upload the changed files
to GitHub (drag-and-drop, **Add file → Upload files**, then commit).
Render automatically redeploys within a minute or two of any GitHub
update — you don't need to repeat the Render setup steps.

## Making the code public later

If you later decide to share the code too: go to your repo on
GitHub → **Settings** → scroll to **Danger Zone** → **Change
visibility** → **Make public**. Render keeps working exactly the
same either way — this only affects whether others can see your code,
not whether the live link works.
