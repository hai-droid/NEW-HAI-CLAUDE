# 05 · תוכנית מדיה

> **התקציב הוא דוגמה:** 150,000 ₪ לשלבים 1–3 (כשמונה שבועות). כל החלוקה באחוזים, כך שאפשר להגדיל או להקטין.

## 1. חלוקה לפי שלב

| שלב | תאריכים | % | ₪ | מטרת אופטימיזציה |
|---|---|---|---|---|
| 1 · פרה-השקה | 12.10–8.11 | 15% | 22,500 | Leads (רשימת המתנה) ובדיקת מסרים |
| 2 · השקה | 9.11–22.11 | 35% | 52,500 | התקנות, ואז `child_linked` |
| 3 · חנוכה | 23.11–12.12 | 50% | 75,000 | `child_linked` ו-`trial_start` |

## 2. חלוקה לפי ערוץ (שלבים 2–3)

| ערוץ | % | תפקיד |
|---|---|---|
| **Meta** (FB + IG) | 40% | נפח, ריטרגטינג, Partnership Ads |
| **Google** (UAC, Search, YouTube) | 30% | כוונה גבוהה (Search), נפח ב-Android (UAC), מודעות (YouTube) |
| **TikTok** | 15% | הורים צעירים (פלח C), Spark Ads |
| **Apple Search Ads** | 10% | iOS, כוונה גבוהה, CPI נמוך |
| **ניסויים** (Taboola, פודקאסטים) | 5% | בדיקה, ומגדילים את מה שעובד |

**בנפרד מתקציב המדיה:** יוצרי תוכן (~15–25K ₪ ל-6–8 יוצרים), יח"צ, והפקת וידאו גיבור.

## 3. מבנה קמפיינים

```
META
├── WK_META_PRE_Leads_IL            (שלב 1, Leads → דף נחיתה)
│   ├── A_Parents_8-12  · B_Parents_Teens · C_Parents_6-8
├── WK_META_LAUNCH_AppInstall_IL    (Advantage+ App, iOS ו-Android בנפרד)
├── WK_META_LAUNCH_Prospecting_IL   (ABO לבדיקת פלחים, 3 סטים × 4 מודעות)
└── WK_META_ALL_Retargeting_IL      (Waitlist, מבקרי אתר, Installed-NoLink)

GOOGLE
├── WK_GADS_UAC_Install_Android     → מעבר ל-child_linked אחרי 30 המרות בשבוע
├── WK_GADS_UAC_Install_iOS
├── WK_GADS_SEARCH_Brand
├── WK_GADS_SEARCH_Generic          (וואטסאפ לילדים...)
├── WK_GADS_SEARCH_Problem          (קבוצת כיתה, מאיזה גיל...)
└── WK_GADS_YT_DemandGen_Parents

TIKTOK
├── WK_TT_LAUNCH_AppInstall_Smart+
└── WK_TT_LAUNCH_Spark_Creators

APPLE SEARCH ADS
├── WK_ASA_Brand · WK_ASA_Category · WK_ASA_Competitor · WK_ASA_Discovery
```

## 4. KPI ויעדים (הערכה ראשונית, לכייל אחרי שבוע)

| מדד | יעד | הערה |
|---|---|---|
| CPL (רשימת המתנה) | 8–15 ₪ | שלב 1 |
| CPI (iOS) | 12–20 ₪ | בישראל iOS יקר יותר |
| CPI (Android) | 6–12 ₪ | |
| Install → child_linked | ≥ 45% | **מדד הבריאות הכי חשוב** |
| עלות להורה פעיל (CPA `child_linked`) | 25–40 ₪ | KPI מוביל |
| Install → trial_start | ≥ 15% | אם יש מודל מנוי `[לאמת]` |
| D7 retention (ילד) | ≥ 35% | |
| K-factor (הזמנות) | ≥ 0.3 | מנגנון "כל הכיתה" |
| CTR Meta | ≥ 1.2% | |
| Thumb-stop (3 ש') TikTok | ≥ 30% | |

**יעד אחרי 8 שבועות (לפי התקציב לדוגמה):** כ-8,000–12,000 התקנות וכ-3,500–5,000 הורים פעילים, לפני האפקט הוויראלי.

## 5. כללי אופטימיזציה
1. **ימים 1–3:** לא נוגעים (תקופת למידה). רק עוצרים מודעה עם CTR מתחת ל-0.5% אחרי 3,000 חשיפות.
2. **ימים 4–7:** מעבירים תקציב לפלח ולקריאייטיב עם CPA `child_linked` הנמוך ביותר. כל פעם משנים ב-20% לכל היותר.
3. **שבוע 2 ואילך:** מעבירים את UAC ואת Meta לאופטימיזציה על `child_linked`. אם אין מספיק נפח, נשארים על install ומשתמשים ב-Value Rules.
4. **iOS:** מסתמכים על SKAN ועל מגמות, לא על מספרים מוחלטים. משווים מול Incrementality (ראו 06).
5. **אחת לשבוע:** דוח MMP מלא: CPA לפי פלח, ערוץ וקריאייטיב, יחד עם Cohort Retention.

## 6. שיבוץ יומי ושבועי
- **שעות שיא להורים:** 20:30–23:00 (אחרי השכבה) ו-12:00–14:00.
- **ימים:** חזק בימים א'–ה'. במוצ"ש מגבירים, ובשישי בערב/שבת מורידים קמפיינים ממוקדים למגזר הדתי `[להחליט]`.
