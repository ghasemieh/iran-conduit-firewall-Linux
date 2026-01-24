#  Iran-Only Firewall for Psiphon Conduit

<div dir="rtl">

## [ فارسی](#راهنمای-فارسی) | [🇬🇧 English](#english-guide)

</div>

---

# English Guide

**Maximize your Psiphon Conduit bandwidth for Iranian users during internet shutdowns.**

When you run a Psiphon Conduit node, people from ANY country can connect. This tool blocks non-Iran IPs so only Iranians can use your bandwidth.

## ✨ Features

- ✅ **Only affects Conduit** - Your PC works normally
- ✅ **2000+ Iran IP ranges** - Updated from authoritative sources  
- ✅ **DNS whitelisted** - Google, Cloudflare, Shekan DNS
- ✅ **Easy toggle** - Enable/disable anytime
- ✅ **Auto-detects Conduit** - Works with Windows Store version

## 📋 Requirements

| Requirement | Details |
|-------------|---------|
| **OS** | Windows 10/11 |
| **Python** | 3.6+ ([Download](https://python.org)) |
| **Conduit** | [Psiphon Conduit](https://conduit.psiphon.ca) |

## 🚀 Quick Start (2 Options)

### Option A: Download ZIP (Easiest)

1. Click **[⬇️ Download ZIP](https://github.com/SamNet-dev/iran-conduit-firewall/archive/refs/heads/master.zip)**
2. Extract the ZIP file
3. Double-click **`RUN_AS_ADMIN.bat`** (auto-elevates to admin)

### Option B: Git Clone

```powershell
git clone https://github.com/SamNet-dev/iran-conduit-firewall.git
cd iran-conduit-firewall
```

Then double-click **`RUN_AS_ADMIN.bat`**

Or run manually as Administrator:
```powershell
python iran_firewall.py
```

## 📖 Usage

```
MAIN MENU
  1. 🟢 Enable Iran-only mode    ← Block non-Iran IPs
  2. 🔴 Disable Iran-only mode   ← Allow all countries
  3. 📊 Check status
  4. 🚀 Conduit management
  0. 🚪 Exit
```

## ❓ FAQ

**Q: Does this affect my PC?**  
A: No! Only Psiphon Conduit is affected.

**Q: Do rules stay after I close the script?**  
A: Yes, until you run option 2 (Disable).

## 📜 License

MIT License - Free to use and share.

---

<div dir="rtl">

# راهنمای فارسی

**پهنای باند Psiphon Conduit خود را برای کاربران ایرانی حداکثر کنید.**

## ✨ ویژگی‌ها

- ✅ **فقط Conduit را تحت تأثیر قرار می‌دهد** - کامپیوتر شما عادی کار می‌کند
- ✅ **بیش از ۲۰۰۰ رنج IP ایران**
- ✅ **DNS های مجاز** - گوگل، کلودفلر، شکن
- ✅ **فعال/غیرفعال آسان**

## 📋 پیش‌نیازها

| پیش‌نیاز | جزئیات |
|----------|--------|
| **سیستم عامل** | ویندوز ۱۰/۱۱ |
| **پایتون** | نسخه ۳.۶+ ([دانلود](https://python.org)) |
| **Conduit** | [Psiphon Conduit](https://conduit.psiphon.ca) |

## 🚀 شروع سریع (۲ روش)

### روش A: دانلود ZIP (آسان‌ترین)

</div>

1. Click **[⬇️ Download ZIP](https://github.com/SamNet-dev/iran-conduit-firewall/archive/refs/heads/master.zip)**

<div dir="rtl">

2. فایل ZIP را استخراج کنید
3. روی **`RUN_AS_ADMIN.bat`** دوبار کلیک کنید

### روش B: Git Clone

</div>

```powershell
git clone https://github.com/SamNet-dev/iran-conduit-firewall.git
cd iran-conduit-firewall
```

<div dir="rtl">

سپس روی **`RUN_AS_ADMIN.bat`** دوبار کلیک کنید

## 📖 استفاده

</div>

```
MAIN MENU
  1. 🟢 Enable Iran-only mode    ← مسدود کردن IP های غیر ایرانی
  2. 🔴 Disable Iran-only mode   ← اجازه به همه کشورها
  3. 📊 Check status
  4. 🚀 Conduit management
  0. 🚪 Exit
```

<div dir="rtl">

## ❓ سؤالات متداول

**س: آیا روی کامپیوتر من تأثیر می‌گذارد؟**  
ج: خیر! فقط Psiphon Conduit تحت تأثیر قرار می‌گیرد.

**س: قوانین بعد از بستن اسکریپت باقی می‌مانند؟**  
ج: بله، تا زمانی که گزینه ۲ را اجرا نکنید.

## 📜 مجوز

MIT License - آزاد برای استفاده و اشتراک‌گذاری.

</div>
