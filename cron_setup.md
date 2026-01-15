# 🕒 Wikipedia Crawler – Cron Job Setup (Updated)

This guide helps you run the Wikipedia crawler automatically on a schedule or every time your Raspberry Pi boots up.

---

## 📁 Project Structure Assumption

Your project is located at:

```
/home/pi/py_crawler/
```

Using a virtual environment:

```
/home/pi/py_crawler/.venv/
```

---

## ✅ Step-by-Step Setup

### 1. Locate Full Paths

Make sure you know the full path to:

- Your Python interpreter (inside your venv):

```bash
which python
# or
echo /home/pi/py_crawler/.venv/bin/python
```

---

### 2. Open Crontab Editor

Run:

```bash
crontab -e
```

If this is your first time, choose the default editor (e.g., `nano`).

---

### 3. Choose a Schedule

#### Option A – Run on Reboot

```cron
@reboot cd /home/pi/py_crawler && /home/pi/py_crawler/.venv/bin/python -m py_crawler.wiki_crawler crawl --limit 100 --depth 2 --topics math,science >> crawler.log 2>&1
```

#### Option B – Run Every Hour

```cron
0 * * * * cd /home/pi/py_crawler && /home/pi/py_crawler/.venv/bin/python -m py_crawler.wiki_crawler crawl --limit 100 --depth 2 --topics math,science >> crawler.log 2>&1
```

#### Option C – Run Every 15 Minutes

```cron
*/15 * * * * cd /home/pi/py_crawler && /home/pi/py_crawler/.venv/bin/python -m py_crawler.wiki_crawler crawl --limit 100 --depth 2 --topics math,science >> crawler.log 2>&1
```

> ✅ `crawler.log` will store all output and errors for debugging

---

### 4. Make Script Executable (Optional)

```bash
chmod +x /home/pi/py_crawler/wiki_crawler.py
```

---

### 5. Test Your Setup

Run manually:

```bash
cd /home/pi/py_crawler
/home/pi/py_crawler/.venv/bin/python -m py_crawler.wiki_crawler crawl --limit 100 --depth 2 --topics math,science
```

Watch live log output:

```bash
tail -f /home/pi/py_crawler/crawler.log
```

---

## 🔄 Optional: Database Backup

Add a weekly backup cron job:

```cron
0 3 * * 0 sqlite3 /home/pi/py_crawler/wiki_links.db ".backup /home/pi/py_crawler/wiki_links_backup.db"
```

---

## 🧠 Tips

- The crawler will automatically resume from where it left off
- You can check status anytime by running:

```bash
python -m py_crawler.status
```

---

## 📘 References

- [Crontab Guru](https://crontab.guru/) — for help writing cron expressions
- `man crontab`

---

## ✅ Done!

You're now set up to run your Wikipedia crawler on a schedule — even automatically at boot.