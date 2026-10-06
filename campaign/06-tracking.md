# 06 · מדידה ותשתית

## 1. סטאק
| רכיב | המלצה | למה |
|---|---|---|
| **MMP** | AppsFlyer או Adjust | שיוך חוצה-ערוצים, SKAN, Deep Links, OneLink להזמנות "כל הכיתה" |
| **Analytics** | Firebase (GA4) | חינמי, מתחבר ל-Google Ads |
| **SDKs לפרסום** | Meta SDK + TikTok Events (דרך ה-MMP, S2S) | |
| **אתר** | Meta Pixel + CAPI, Google Tag, TikTok Pixel | לרשימת ההמתנה ולריטרגטינג |
| **Deep Links** | OneLink / Adjust Links | הזמנה לקבוצת כיתה שפותחת את האפליקציה ישר בקבוצה |

> ⚠️ **SDKs ופרטיות ילדים:** האירועים נשלחים **רק מהצד של ההורה** (חשבון ההורה, 18+). ממכשיר הילד או מחשבון הילד **לא מעבירים שום מזהה פרסומי** לפלטפורמות פרסום. זה קריטי ל-COPPA, לחוק הגנת הפרטיות (תיקון 13) ולמדיניות Apple Kids ו-Google Families. מומלץ לבנות **אפליקציה או פרופיל נפרד להורה**, או לכבות את ה-SDKs במצב ילד `[לאמת ארכיטקטורה]`.

## 2. אירועים (Event Taxonomy)

| אירוע | מתי | שולחים ל- | הערה |
|---|---|---|---|
| `install` | התקנה ראשונה | הכל | אוטומטי |
| `parent_signup` | הורה סיים הרשמה | הכל | |
| `child_profile_created` | נוצר פרופיל ילד | MMP + Firebase | בלי פרטי ילד! רק `child_age_band` (6-8/8-11/11-14) |
| **`child_linked`** | מכשיר הילד חובר | **הכל, וזה אירוע האופטימיזציה הראשי** | |
| `first_message` | הילד שלח הודעה ראשונה (נספר בצד השרת) | MMP S2S | מאגרגציה בלבד |
| `contact_approved` | ההורה אישר איש קשר | MMP | מדד מעורבות |
| `class_invite_sent` | נשלחה הזמנת "כל הכיתה" | MMP | למדידת K-factor |
| `class_invite_joined` | הורה הצטרף מהזמנה | MMP | |
| `trial_start` | התחלת ניסיון | הכל | `[לאמת מודל]` |
| `subscribe` | תשלום ראשון | הכל + value | `[לאמת מודל]` |

## 3. SKAdNetwork / AdAttributionKit (iOS)
סכמת Conversion Value מוצעת (חלון ראשון, 0–48 שעות):
| CV (coarse) | תנאי |
|---|---|
| low | install + parent_signup |
| medium | child_linked |
| high | child_linked + first_message, או trial_start |

## 4. UTM ומוסכמות שמות

**קמפיין:** `WK_{ערוץ}_{שלב}_{מטרה}_{מיקום}` → `WK_META_LAUNCH_AppInstall_IL`
**סט/קבוצה:** `{פלח}_{טרגוט}` → `A_Parents_8-12`
**מודעה:** `{קונספט}_{וריאציה}_{פורמט}_{תאריך}` → `C1-Group_HookB_9x16_1109`

**UTM לאתר:**
```
utm_source=meta|google|tiktok|taboola|creator_{name}|parents_committee
utm_medium=paid_social|cpc|video|native|influencer|referral
utm_campaign=wk_launch_2026
utm_content={שם המודעה}
utm_term={פלח או מילת מפתח}
```

## 5. מדידת Incrementality
- **Geo-holdout:** בשבועות 3–4 של ההשקה, אזור אחד (למשל באר שבע והדרום) בלי Meta במשך שבועיים. משווים התקנות אורגניות.
- **Brand Lift:** בסקר של Meta ו-YouTube Brand Lift בשלב 3, אם התקציב עומד בסף המינימום.
- שאלת **"איך שמעתם עלינו?"** במסך ההרשמה, כדי לתפוס מפה לאוזן ושגרירים.

## 6. דשבורד שבועי (תבנית)
| ערוץ | הוצאה | התקנות | CPI | child_linked | CPA | % Link | D7 | הזמנות | K |
|---|---|---|---|---|---|---|---|---|---|
| Meta | | | | | | | | | |
| Google | | | | | | | | | |
| TikTok | | | | | | | | | |
| ASA | | | | | | | | | |
| אורגני/הפניות | – | | – | | – | | | | |
