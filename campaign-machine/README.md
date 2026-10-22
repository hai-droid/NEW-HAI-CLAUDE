# 🏢 מכונת הקמפיינים – מחלקת שיווק של סוכני AI על המחשב שלך

שישה סוכני AI שעובדים ביחד בתוך **Claude Code**: אתה כותב בקשה בעברית, הם בונים, ואתה בודק ומאשר.

```
בריף ─▶ 👔 מנכ"ל ─▶ ✍️ קופירייטרית ─▶ 🎨 קריאייטיבית  ┐
                                    🖥️ דף נחיתה      ┴─▶ 🧑 אתה מאשר ─▶ 🚀 קמפיינר ─▶ Meta (PAUSED)
                                                                                  │
            ◀── משימות תיקון ◀── 📊 אנליסט ◀── נתונים מ-Meta ◀───────────────────┘
```

| סוכן | מה הוא עושה | קובץ |
|---|---|---|
| 👔 המנכ"ל | מקבל בריף, קובע אסטרטגיה וזוויות, מחלק משימות לצוות | `.claude/agents/ceo.md` |
| ✍️ הקופירייטרית | זוויות, 5+ הוקים ומודעות בקול של המותג | `.claude/agents/copywriter.md` |
| 🎨 הקריאייטיבית | 5 קריאייטיבים במקביל, במיתוג שלך, עם עברית תקינה | `.claude/agents/creative.md` |
| 🖥️ בונה דפי הנחיתה | דף אמיתי עם טופס לידים ופיקסל, ומעלה לאוויר | `.claude/agents/landing.md` |
| 🚀 הקמפיינר | בונה את הקמפיין ב-Meta, תמיד במצב PAUSED | `.claude/agents/campaigner.md` |
| 📊 האנליסט | קורא נתונים, כותב מסקנות והופך כל מסקנה למשימה | `.claude/agents/analyst.md` |

ובונוס: **משרד הסוכנים** – חדר בקרה חי ב-http://localhost:3000/office שמראה מי עובד, על מה, ומה כבר יצא.

---

## 1. מה צריך (ועלויות)

| דבר | למה | עלות |
|---|---|---|
| מנוי Claude (Pro / Max) או מפתח API | Claude Code – המוח של כל הסוכנים | לפי המנוי |
| חשבון Meta Business + חשבון מודעות | הקמפיינים | תקציב הפרסום שלך |
| מפתח OpenAI או Gemini (לא חובה) | רקעים בתמונות AI לקריאייטיבים | בערך 0.04$–0.2$ לתמונה |
| חשבון Vercel (לא חובה) | העלאת דפי נחיתה לאוויר | חינם לשימוש רגיל |
| Make / Zapier / Google Sheets | לאן הלידים מהטופס נשמרים | יש מסלולים חינמיים |

בלי שום מפתח חוץ מ-Claude אפשר כבר להריץ הכל עד שלב ה-Dry Run: קופי, קריאייטיבים (ברקע במיתוג), דף נחיתה ותוכנית קמפיין.

---

## 2. התקנה

### Windows
1. הורד את התיקייה `campaign-machine` למחשב (או `git clone` של הריפו).
2. לחיצה כפולה על **`install-windows.bat`**. הוא מתקין Git, Node.js, Python ו-Claude Code (דרך winget) ואת ספריות הפייתון.
   - אם הוא מבקש – סגור את החלון, פתח חדש והרץ שוב (אחרי התקנת Python).
3. פתח את `.env` ב-Notepad ומלא מפתחות (פרק 4).

### Mac
1. התקן Python מ-https://www.python.org/downloads ו-Node.js LTS מ-https://nodejs.org.
2. ב-Terminal, בתוך התיקייה: `bash install-mac.sh`
3. `open -e .env` ומלא מפתחות (פרק 4).

### הפעלה
פתח טרמינל בתוך התיקייה `campaign-machine` והקלד:
```
claude
```
בפעם הראשונה תתבקש להתחבר לחשבון Claude, ולאשר שאתה סומך על התיקייה (זה טוען את הסוכנים, הסקילים והבלמים).

---

## 3. הרצה ראשונה – על לקוח הדמו (בלי מפתחות)

יש בפרויקט לקוח בדיוני: `clients/demo-studio` (סטודיו פילאטיס). בתוך Claude Code:

```
/office
/campaign demo-studio
```

ותראה את הצוות עובד: המנכ"ל כותב `tasks.json`, הקופירייטרית 5 הוקים, הקריאייטיבית ודף הנחיתה רצים במקביל, והקמפיינר מציג Dry Run ועוצר לאישור שלך. בלי חיבור ל-Meta שום דבר לא נשלח לשום מקום.

רוצה לבדוק את הכלים בלי Claude בכלל?
```
python tools/images.py batch --client demo-studio --campaign 2026-10-22-intro-offer
python tools/meta.py launch  --client demo-studio --campaign 2026-10-22-intro-offer
python tools/office.py
```
(ב-Mac: `python3`)

---

## 4. חיבורים

### Meta (החלק שכולם נתקעים בו – צעד אחרי צעד)
1. **Business Manager:** https://business.facebook.com → ודא שיש לך עסק, **עמוד פייסבוק** ו**חשבון מודעות** עם אמצעי תשלום.
2. **System User:** הגדרות העסק → משתמשים → **System users** → Add → תפקיד Admin.
3. **שיוך נכסים:** על ה-System User → **Assign assets** → חשבון המודעות (Manage ad account), העמוד, והפיקסל.
4. **אפליקציה:** https://developers.facebook.com/apps → Create app → סוג **Business** → שייך לעסק → הוסף את המוצר **Marketing API**.
5. **טוקן:** חזרה ל-System User → **Generate new token** → בחר את האפליקציה → הרשאות: `ads_management`, `ads_read`, `business_management`, `pages_read_engagement`, `pages_show_list` → תוקף: **Never**.
6. הדבק את הטוקן ב-`.env`: `META_ACCESS_TOKEN=...` (לעולם לא בצ'אט ולא ב-Git).
7. **מזהים** – הכנס ל-`clients/<client>/config.json`:
   - `ad_account_id` – ב-Ads Manager, המספר ליד שם החשבון (אפשר עם או בלי `act_`)
   - `page_id` – בעמוד → אודות → מזהה עמוד
   - `pixel_id` – Events Manager → מקורות נתונים → הפיקסל
   - `instagram_user_id` – (לא חובה) הגדרות העסק → חשבונות אינסטגרם
8. בדיקה: `python tools/meta.py check --client <client>` צריך להחזיר ✓ על החשבון, העמוד והפיקסל.

### לאן הלידים הולכים (webhook)
הטופס בדף שולח כל ליד ל-`landing.lead_webhook_url` ב-`config.json`. הכי פשוט – **Google Sheets**:
1. צור גיליון, ובו לשונית בשם `Leads`.
2. הרחבות → **Apps Script**, הדבק:
   ```js
   function doPost(e) {
     const d = JSON.parse(e.postData.contents);
     SpreadsheetApp.getActive().getSheetByName('Leads').appendRow([
       new Date(), d.name, d.phone, d.email, d.campaign, d.utm_content, d.page
     ]);
     return ContentService.createTextOutput('ok');
   }
   ```
3. Deploy → New deployment → **Web app** → Execute as: Me → Who has access: **Anyone** → העתק את ה-URL ל-`lead_webhook_url`.

(או: Webhook ב-Make / Zapier, ומשם ל-CRM, וואטסאפ, מייל.)

### Vercel (העלאת דפים)
פעם אחת בטרמינל: `npx vercel login`. אחר כך הסוכן מעלה עם `landing.py deploy` – ותמיד מבקש אישור.

### תמונות AI (לא חובה)
ב-`.env`: `IMAGE_PROVIDER=openai` + `OPENAI_API_KEY=...` או `IMAGE_PROVIDER=gemini` + `GEMINI_API_KEY=...`.
ה-AI מייצר רק **רקע בלי טקסט**, והכלי מניח עליו את הכותרת בעברית, הכפתור והלוגו – כך שהעברית תמיד תקינה.

---

## 5. עבודה יומיומית

| פקודה | מה קורה |
|---|---|
| `/new-client yoga-tlv https://site.co.il` | תיקייה חדשה ללקוח + ראיון שממלא עסק, קול מותג והגדרות |
| `/interview yoga-tlv` | בריף לקמפיין חדש |
| `/campaign yoga-tlv וובינר ב-12.11` | כל הצוות, מבריף ועד קמפיין מוכן ב-PAUSED |
| `/analyze yoga-tlv` | האנליסט קורא נתונים, ומשימות תיקון חוזרות לצוות |
| `/office` | משרד הסוכנים |
| `/checkpoint save לפני שינוי גדול` | נקודת שמירה (git). גם `list` ו-`reset` |

אפשר גם פשוט לכתוב בעברית: *"תן לקופירייטרית לכתוב 5 הוקים חדשים לזווית הכאב"*, *"הקריאייטיבית – 3 גרסאות של c2 ברקע בהיר"*.

---

## 6. בלמי הבטיחות

הבלמים כתובים **בקוד** (`tools/meta.py`, `tools/guard.py`, `.claude/settings.json`) – לא בהנחיות לסוכן, כך שהוא לא יכול "להחליט" לעקוף אותם.

| # | בלם | איך |
|---|---|---|
| 1 | כל קמפיין, ad set ומודעה נוצרים **PAUSED** | קבוע בקוד. לכלי אין בכלל פקודת הפעלה – אתה מפעיל ב-Ads Manager |
| 2 | **תקרת תקציב** יומית וכוללת | `safety` ב-config של הלקוח. חריגה = הכלי מסרב |
| 3 | **Dry Run** | בלי `--execute` שום דבר לא נשלח. רואים בדיוק מה ייווצר |
| 4 | **אישור מפורש** | `--execute`, העלאת דף, git reset → חלון אישור של Claude Code |
| 5 | **חסימת מחיקה** | אין בקוד שום בקשת DELETE, וה-hook חוסם ניסיון כזה |
| 6 | **Checkpoints ו-Reset** | `/checkpoint` (git) + גם הריוויינד המובנה של Claude Code (Esc Esc) |
| 7 | **רק API רשמי** | גישה ישירה ל-graph.facebook.com מחוץ לכלי – חסומה |
| 8 | **סודות אצלך** | `.env` ב-gitignore, והסוכן חסום מלקרוא או להדפיס אותו |
| 9 | **הפרדה בין לקוחות** | כל לקוח בתיקייה משלו. הכלים חוסמים נתיב שיוצא מתיקיית הלקוח |

כל פעולת כתיבה ב-Meta נרשמת ב-`clients/<client>/meta-log.jsonl`.

> המערכת לא מחליפה שיקול דעת. האחריות על חשבון הפרסום ועל התקציב היא שלך – ולכן אתה בלולאה בכל שלב שנוגע בכסף.

---

## 7. מבנה הפרויקט

```
campaign-machine/
├─ CLAUDE.md                 חוקי הפרויקט שכל סוכן קורא
├─ .claude/
│  ├─ agents/                ששת הסוכנים
│  ├─ skills/                /campaign /analyze /new-client /interview /office /checkpoint
│  └─ settings.json          הרשאות + hooks (הבלמים)
├─ tools/                    כלי פייתון: meta, images, landing, office, guard
├─ templates/landing.html    תבנית דף נחיתה RTL
├─ clients/
│  ├─ _template/             שלד ללקוח חדש
│  └─ demo-studio/           לקוח דמו
│     ├─ business.md  brand-voice.md  config.json  assets/
│     └─ campaigns/2026-10-22-intro-offer/ ...
├─ fonts/                    פונט עברי לקריאייטיבים (ראה fonts/README.md)
└─ office/                   יומן האירועים של משרד הסוכנים
```

לקוח חדש = תיקייה חדשה. אותו צוות, אפס בנייה מחדש.

---

## 8. תקלות נפוצות

| תקלה | פתרון |
|---|---|
| `python` / `python3` לא נמצא | Windows: התקן Python וסמן "Add to PATH". Mac: התקן מ-python.org |
| העברית בתמונה הפוכה | `pip install -r requirements.txt` (python-bidi) |
| `Meta החזירה שגיאה (190)` | הטוקן לא תקין או פג. צור חדש ב-System User |
| `(100) Invalid parameter` | בדוק את ה-IDs ב-config.json, ושהפיקסל משויך ל-System User |
| שגיאה על `META_API_VERSION` | עדכן ב-.env לגרסה הנוכחית (https://developers.facebook.com/docs/graph-api/changelog) |
| הסוכנים לא מופיעים | ודא שהפעלת את `claude` מתוך התיקייה `campaign-machine`, ואישרת trust |
| פורט 3000 תפוס | `python tools/office.py 3001` |

> **הערה כנה:** הכלים נבדקו על Dry Run, יצירת קריאייטיבים, דף נחיתה, ה-hooks ומשרד הסוכנים. החיבור החי ל-Meta לא נבדק מול חשבון אמיתי – בהרצה הראשונה התחל בתקציב קטן, בדוק כל דבר ב-Ads Manager לפני הפעלה, ואם Meta מחזירה שגיאה, הדבק אותה ל-Claude והוא יתקן.
