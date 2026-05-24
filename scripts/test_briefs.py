"""
ARQA Phase 1 — Day 9
Annotated test set for evaluating Communication Agent extraction
across English, Urdu, and Arabic — including code-switched and
romanized forms that real users in Pakistan/Gulf actually write.

Each entry has:
  - id, language (expected), type
  - brief: the input text
  - expected: ground-truth values for KEY fields we score against

NOTE: These are SYNTHETIC but realistic briefs, constructed for
evaluation (documented limitation — real-user briefs are future work).
Urdu/Roman-Urdu validated by a native speaker; Arabic/Roman-Arabic
should ideally be validated by a native Gulf speaker (limitation).
"""

TEST_BRIEFS = [
    # ---------- ENGLISH ----------
    {
        "id": "en_clean",
        "language": "english",
        "type": "clean",
        "brief": (
            "I want to build a 4 bedroom villa in Riyadh. Budget around "
            "1.5 to 2 million riyals, 2 to 3 storeys, 3 bathrooms, a kitchen, "
            "a living room, and a separate majlis for male guests. Family "
            "privacy is important and a separate entrance for women."
        ),
        "expected": {
            "country": "saudi_arabia",
            "project_type": "villa",
            "currency": "SAR",
            "bedrooms": 4,
            "has_majlis": True,
            "cultural_flags_any": True,
            "ready_for_design": True,
        },
    },
    {
        "id": "en_messy",
        "language": "english",
        "type": "messy",
        "brief": (
            "looking for a biggish family home, maybe 3 or 4 beds, ground "
            "plus one, nothing fancy, budget not sure maybe 800k-ish, want "
            "privacy from the street and somewhere to receive male guests."
        ),
        "expected": {
            "country": None,
            "currency": None,
            "has_majlis": True,
            "cultural_flags_any": True,
            "ready_for_design": False,
        },
    },

    # ---------- URDU (script) ----------
    {
        "id": "ur_clean",
        "language": "urdu",
        "type": "clean",
        "brief": (
            "مجھے لاہور میں ایک 5 بیڈروم کا گھر بنانا ہے۔ بجٹ تقریباً 2 کروڑ "
            "روپے ہے، 2 منزلہ، 3 باتھ روم، ایک کچن، ایک ڈرائنگ روم اور "
            "مہمانوں کے لیے الگ بیٹھک۔ فیملی کی پرائیویسی بہت اہم ہے۔"
        ),
        "expected": {
            "country": "pakistan",
            "project_type": "house",
            "currency": "PKR",
            "bedrooms": 5,
            "has_majlis": True,
            "cultural_flags_any": True,
            "ready_for_design": True,
        },
    },
    {
        "id": "ur_messy",
        "language": "urdu",
        "type": "messy",
        "brief": (
            "ایک اچھا سا فیملی گھر چاہیے، شاید 3 یا 4 کمرے، زیادہ مہنگا نہیں، "
            "بجٹ کا پکا نہیں، اور سڑک سے پرائیویسی ہونی چاہیے۔"
        ),
        "expected": {
            "country": None,
            "currency": None,
            "cultural_flags_any": True,
            "ready_for_design": False,
        },
    },

    # ---------- ARABIC (script) ----------
    {
        "id": "ar_clean",
        "language": "arabic",
        "type": "clean",
        "brief": (
            "أريد بناء فيلا من 4 غرف نوم في دبي. الميزانية حوالي 2 إلى 3 "
            "مليون درهم، طابقين، 3 حمامات، مطبخ، صالة، ومجلس منفصل للضيوف "
            "الرجال. خصوصية العائلة مهمة جداً ومدخل منفصل للنساء."
        ),
        "expected": {
            "country": "uae",
            "project_type": "villa",
            "currency": "AED",
            "bedrooms": 4,
            "has_majlis": True,
            "cultural_flags_any": True,
            "ready_for_design": True,
        },
    },
    {
        "id": "ar_messy",
        "language": "arabic",
        "type": "messy",
        "brief": (
            "أبحث عن منزل عائلي كبير نوعاً ما، ربما 3 أو 4 غرف، ليس فخماً، "
            "الميزانية غير محددة، وأريد خصوصية عن الشارع ومكان لاستقبال الضيوف."
        ),
        "expected": {
            "country": None,
            "currency": None,
            "cultural_flags_any": True,
            "ready_for_design": False,
        },
    },

    # ---------- CODE-SWITCHED (real-world mixing) ----------
    {
        "id": "ur_mixed",
        "language": "urdu",
        "type": "code_switched",
        "brief": (
            "مجھے Lahore میں ایک 4 bedroom کا villa بنانا ہے۔ budget تقریباً "
            "2 crore rupees، 2 floors، 3 bathrooms، ایک kitchen، اور guests "
            "کے لیے ایک separate majlis۔ family privacy بہت important ہے۔"
        ),
        "expected": {
            "country": "pakistan",
            "project_type": "villa",
            "currency": "PKR",
            "bedrooms": 4,
            "has_majlis": True,
            "cultural_flags_any": True,
            "ready_for_design": True,
        },
    },
    {
        "id": "ar_mixed",
        "language": "arabic",
        "type": "code_switched",
        "brief": (
            "أريد villa من 4 bedrooms في دبي. الـ budget حوالي 2 million "
            "dirham، طابقين، 3 bathrooms، kitchen، و majlis منفصل للـ guests. "
            "الـ privacy للعائلة مهمة جداً."
        ),
        "expected": {
            "country": "uae",
            "project_type": "villa",
            "currency": "AED",
            "bedrooms": 4,
            "has_majlis": True,
            "cultural_flags_any": True,
            "ready_for_design": True,
        },
    },

    # ---------- ROMAN URDU (Urdu language, Latin script — very common in Pakistan) ----------
    {
        "id": "ur_roman",
        "language": "urdu",
        "type": "roman_urdu",
        "brief": (
            "mujhe Lahore mein 5 marla ka ghar banana hai, jo ke 2 stories "
            "mein ho, 3 bedroom hon, ek kitchen aur 2 bathroom hon. mehmano "
            "ke liye alag baithak bhi honi chahiye aur family privacy zaroori hai."
        ),
        "expected": {
            "country": "pakistan",
            "project_type": "house",
            "bedrooms": 3,
            "has_majlis": True,
            "cultural_flags_any": True,
            "ready_for_design": True,
        },
    },

    # ---------- ROMAN ARABIC / "Arabizi" (Arabic language, Latin + numerals) ----------
    {
        "id": "ar_roman",
        "language": "arabic",
        "type": "roman_arabic",
        "brief": (
            "abi abni villa fi Dubai, 4 ghuraf nom, el budget 7awali 2 "
            "million dirham, taba2een, 3 7ammamat, matbakh, w majlis "
            "munfasil lel duyoof. khususiyat el 3a2ila muhimma jiddan."
        ),
        "expected": {
            "country": "uae",
            "project_type": "villa",
            "bedrooms": 4,
            "has_majlis": True,
            "cultural_flags_any": True,
            "ready_for_design": True,
        },
    },
]