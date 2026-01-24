# 🇮🇷 Iran-Only Firewall for Psiphon Conduit

<div dir="rtl">

## [🇮🇷 فارسی](#راهنمای-فارسی) | [🇬🇧 English](#english-guide)

</div>

---

# English Guide

**Maximize your Psiphon Conduit bandwidth for Iranian users during internet shutdowns.**

When you run a Psiphon Conduit node, people from ANY country can connect. This tool blocks non-Iran IPs so only Iranians can use your bandwidth.

## ✨ Features

- ✅ **Only affects Conduit** - Your PC works normally
- ✅ **2000+ Iran IP ranges** - Updated from authoritative sources
- ✅ **DNS whitelisted** - Google, Cloudflare, Shekan DNS
- ✅ **Easy toggle** - Enable/disable with one click
- ✅ **Auto-detects Conduit** - Works with Windows Store version

## 📋 Requirements

| Requirement | Details |
|-------------|---------|
| **OS** | Windows 10/11 |
| **Python** | 3.6+ ([Download](https://python.org)) |
| **Conduit** | [Psiphon Conduit](https://conduit.psiphon.ca) |
| **Permissions** | Run as Administrator |

## 🚀 Quick Start

### 1. Download
```
git clone https://github.com/SamNet-dev/iran-conduit-firewall.git
cd iran-conduit-firewall
```

### 2. Run as Administrator
```powershell
# Right-click PowerShell → Run as Administrator
python iran_firewall.py
```

### 3. Enable Iran-Only Mode
- Choose option `1` from the menu
- Wait for IP ranges to download
- Done! Only Iranian users can connect

## 📖 Usage

```
MAIN MENU
  1. 🟢 Enable Iran-only mode    ← Block non-Iran IPs
  2. 🔴 Disable Iran-only mode   ← Allow all countries
  3. 📊 Check status             ← See current state
  4. 🚀 Conduit management       ← Start/stop Conduit
  5. ❓ Help
  0. 🚪 Exit
```

## ❓ FAQ

**Q: Does this affect my PC?**  
A: No! Only Psiphon Conduit is affected. Your browsing, apps, and everything else works normally.

**Q: Do rules stay after I close the script?**  
A: Yes, firewall rules persist until you run option 2 (Disable).

**Q: No connections after enabling?**  
A: Normal! It may take time for Iranian users to be routed to your node.

## 📜 License

MIT License - Free to use and share.

---

<div dir="rtl">

# راهنمای فارسی

**پهنای باند Psiphon Conduit خود را برای کاربران ایرانی در زمان قطعی اینترنت حداکثر کنید.**

وقتی یک نود Psiphon Conduit اجرا می‌کنید، افراد از هر کشوری می‌توانند متصل شوند. این ابزار IP های غیر ایرانی را مسدود می‌کند تا فقط ایرانی‌ها بتوانند از پهنای باند شما استفاده کنند.

## ✨ ویژگی‌ها

- ✅ **فقط Conduit را تحت تأثیر قرار می‌دهد** - کامپیوتر شما عادی کار می‌کند
- ✅ **بیش از ۲۰۰۰ رنج IP ایران** - به‌روز از منابع معتبر
- ✅ **DNS های مجاز** - گوگل، کلودفلر، شکن
- ✅ **فعال/غیرفعال آسان** - با یک کلیک
- ✅ **تشخیص خودکار Conduit** - با نسخه Windows Store کار می‌کند

## 📋 پیش‌نیازها

| پیش‌نیاز | جزئیات |
|----------|--------|
| **سیستم عامل** | ویندوز ۱۰/۱۱ |
| **پایتون** | نسخه ۳.۶+ ([دانلود](https://python.org)) |
| **Conduit** | [Psiphon Conduit](https://conduit.psiphon.ca) |
| **دسترسی** | اجرا به عنوان Administrator |

## 🚀 شروع سریع

### ۱. دانلود
</div>

```
git clone https://github.com/SamNet-dev/iran-conduit-firewall.git
cd iran-conduit-firewall
```

<div dir="rtl">

### ۲. اجرا به عنوان Administrator

</div>

```powershell
# کلیک راست روی PowerShell → Run as Administrator
python iran_firewall.py
```

<div dir="rtl">

### ۳. فعال کردن حالت فقط ایران
- گزینه `1` را از منو انتخاب کنید
- منتظر دانلود رنج‌های IP بمانید
- تمام! فقط کاربران ایرانی می‌توانند متصل شوند

## 📖 استفاده

</div>

```
MAIN MENU
  1. 🟢 Enable Iran-only mode    ← مسدود کردن IP های غیر ایرانی
  2. 🔴 Disable Iran-only mode   ← اجازه به همه کشورها
  3. 📊 Check status             ← مشاهده وضعیت فعلی
  4. 🚀 Conduit management       ← شروع/توقف Conduit
  5. ❓ Help
  0. 🚪 Exit
```

<div dir="rtl">

## ❓ سؤالات متداول

**س: آیا این روی کامپیوتر من تأثیر می‌گذارد؟**  
ج: خیر! فقط Psiphon Conduit تحت تأثیر قرار می‌گیرد. مرورگر، برنامه‌ها و همه چیز عادی کار می‌کند.

**س: آیا قوانین بعد از بستن اسکریپت باقی می‌مانند؟**  
ج: بله، قوانین فایروال تا زمانی که گزینه ۲ (غیرفعال) را اجرا نکنید باقی می‌مانند.

**س: بعد از فعال کردن هیچ اتصالی ندارم؟**  
ج: عادی است! ممکن است زمان ببرد تا کاربران ایرانی به نود شما هدایت شوند.

## 📜 مجوز

MIT License - آزاد برای استفاده و اشتراک‌گذاری.

</div>
