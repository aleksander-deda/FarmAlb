"""
Dev seed — roles, permissions, users, vendors, experiences, products, promotions.
Run: python -m app.db.seed
"""
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.identity import Role, Permission, RolePermission, User, UserRole
from app.models.catalog import Vendor, Experience, ExperienceSlot, Product, Promotion
from app.core.security import hash_password
from datetime import datetime, timezone, timedelta
import re


# ── Roles ──────────────────────────────────────────────────────────────────────
ROLES = [
    {"code": "SUPER_ADMIN",  "name": "Super Admin",  "description": "Full platform access"},
    {"code": "VENDOR_ADMIN", "name": "Vendor Admin",  "description": "Manages a single vendor"},
    {"code": "VENDOR_STAFF", "name": "Vendor Staff",  "description": "Limited vendor access"},
    {"code": "GUEST",        "name": "Guest",          "description": "Registered customer"},
]

# ── Permissions ────────────────────────────────────────────────────────────────
PERMISSIONS = [
    {"code": "BOOKING_READ",   "resource": "booking",  "action": "read"},
    {"code": "BOOKING_CREATE", "resource": "booking",  "action": "create"},
    {"code": "BOOKING_CANCEL", "resource": "booking",  "action": "cancel"},
    {"code": "PRODUCT_READ",   "resource": "product",  "action": "read"},
    {"code": "PRODUCT_CREATE", "resource": "product",  "action": "create"},
    {"code": "PRODUCT_UPDATE", "resource": "product",  "action": "update"},
    {"code": "PRODUCT_DELETE", "resource": "product",  "action": "delete"},
    {"code": "VENDOR_READ",    "resource": "vendor",   "action": "read"},
    {"code": "VENDOR_APPROVE", "resource": "vendor",   "action": "approve"},
    {"code": "VENDOR_SUSPEND", "resource": "vendor",   "action": "suspend"},
    {"code": "PAYOUT_READ",    "resource": "payout",   "action": "read"},
    {"code": "PAYOUT_APPROVE", "resource": "payout",   "action": "approve"},
    {"code": "USER_READ",      "resource": "user",     "action": "read"},
    {"code": "USER_SUSPEND",   "resource": "user",     "action": "suspend"},
]

ROLE_PERMISSIONS = {
    "SUPER_ADMIN":  [p["code"] for p in PERMISSIONS],
    "VENDOR_ADMIN": ["BOOKING_READ", "BOOKING_CANCEL", "PRODUCT_READ",
                     "PRODUCT_CREATE", "PRODUCT_UPDATE", "PRODUCT_DELETE", "PAYOUT_READ"],
    "VENDOR_STAFF": ["BOOKING_READ", "PRODUCT_READ", "PRODUCT_UPDATE"],
    "GUEST":        ["BOOKING_READ", "BOOKING_CREATE", "BOOKING_CANCEL", "PRODUCT_READ"],
}

# ── Users ──────────────────────────────────────────────────────────────────────
USERS = [
    {
        "full_name": "Admin FarmaAlb",
        "email": "admin@farmalb.al",
        "password": "admin1234",
        "status": "active",
        "is_superuser": True,
        "role_code": "SUPER_ADMIN",
    },
    {
        "full_name": "Ceren Ismet Shehu",
        "email": "ceren@farmalb.al",
        "password": "vendor1234",
        "status": "active",
        "is_superuser": False,
        "role_code": "VENDOR_ADMIN",
    },
    {
        "full_name": "Bledi Sulo",
        "email": "bledi@farmalb.al",
        "password": "vendor1234",
        "status": "active",
        "is_superuser": False,
        "role_code": "VENDOR_ADMIN",
    },
    {
        "full_name": "Ardit Kelmendi",
        "email": "ardit@farmalb.al",
        "password": "guest1234",
        "status": "active",
        "is_superuser": False,
        "role_code": "GUEST",
    },
    {
        "full_name": "Besa Leka",
        "email": "besa@farmalb.al",
        "password": "guest1234",
        "status": "active",
        "is_superuser": False,
        "role_code": "GUEST",
    },
]

# ── Vendors ────────────────────────────────────────────────────────────────────
VENDORS = [
    {
        "owner_email": "ceren@farmalb.al",
        "name": "Ceren — Ismet Shehu",
        "slug": "ceren-ismet-shehu",
        "type": "AGRITOURISM",
        "status": "active",
        "tier": "PRO",
        "region": "Lezha",
        "address": "Shëngjin, Lezha, Shqipëri",
        "lat": 41.8075,
        "lng": 19.5942,
        "description": (
            "Një nga destinacionet më të njohura agriturizmike në Shqipëri. "
            "Familja Shehu ofron ushqim tradicional shqiptar të gatuar me produkte "
            "nga toka e tyre — mish, djathë, mjaltë dhe perime të sezonit. "
            "Ambienti rural, mikpritja e ngrohtë dhe shija autentike e bëjnë "
            "Ceren një përvojë të paharruar."
        ),
        "website": "https://ceren.al",
        "phone": "+355 69 123 4567",
        "email": "info@ceren.al",
    },
    {
        "owner_email": "bledi@farmalb.al",
        "name": "Mrizi i Zanave",
        "slug": "mrizi-i-zanave",
        "type": "AGRITOURISM",
        "status": "active",
        "tier": "PRO",
        "region": "Lezha",
        "address": "Fishtë, Lezha, Shqipëri",
        "lat": 41.7523,
        "lng": 19.6891,
        "description": (
            "Mrizi i Zanave është shumë më tepër se një restorant — është një filozofi. "
            "I themeluar nga Altin Prenga, ky agroturizëm ka revolucionarizuar "
            "kuzhinën shqiptare duke u kthyer te rrënjët: produkte lokale, receta "
            "tradicionale dhe respekt i thellë për natyrën. Njihet si restoranti "
            "më i mirë rural i Shqipërisë."
        ),
        "website": "https://mrizizanave.com",
        "phone": "+355 69 234 5678",
        "email": "info@mrizizanave.com",
    },
    {
        "owner_email": "admin@farmalb.al",
        "name": "Kantina Çobo Winery",
        "slug": "cantina-cobo-winery",
        "type": "WINERY",
        "status": "active",
        "tier": "PRO",
        "region": "Berati",
        "address": "Çobo, Berat, Shqipëri",
        "lat": 40.7058,
        "lng": 19.9522,
        "description": (
            "Kantina Çobo është një nga prodhuesit më të shquar të verës në Shqipëri, "
            "e specializuar në varietetin autoktone Shesh i Zi. E vendosur në zemrën "
            "e Beratit — qytetit të njëmijë dritareve — kantina ofron turne guidate "
            "nëpër vreshta dhe degutime ekskluzive të verërave fisnike."
        ),
        "website": "https://cobowinery.com",
        "phone": "+355 68 345 6789",
        "email": "info@cobowinery.com",
    },
    {
        "owner_email": "admin@farmalb.al",
        "name": "Ferma Organike Gomsiqe",
        "slug": "ferma-organike-gomsiqe",
        "type": "FARM",
        "status": "active",
        "tier": "FREE",
        "region": "Shkodra",
        "address": "Gomsiqe, Shkodër, Shqipëri",
        "lat": 42.0683,
        "lng": 19.5126,
        "description": (
            "Ferma Organike Gomsiqe shtrihet në luginën e bukur të Shkodrës, "
            "rrethuar nga malet e Alpeve Shqiptare. Produktet tona organike — "
            "mjaltë, djathë, fruta dhe perime — kultivohen pa kimikate, "
            "sipas traditave shekullore të zonës. Vizitorët mund të marrin "
            "pjesë në jetën e fermës dhe të kuptojnë nga afër procesin e prodhimit."
        ),
        "website": "",
        "phone": "+355 67 456 7890",
        "email": "ferma.gomsiqe@gmail.com",
    },
    {
        "owner_email": "admin@farmalb.al",
        "name": "Vreshtaria Nurellari",
        "slug": "vreshtaria-nurellari",
        "type": "WINERY",
        "status": "active",
        "tier": "FREE",
        "region": "Vlora",
        "address": "Nartë, Vlorë, Shqipëri",
        "lat": 40.5283,
        "lng": 19.4891,
        "description": (
            "Vreshtaria Nurellari ndodhet pranë lagunës së Nartës, "
            "një nga ekosistemet më të pasura të Shqipërisë. "
            "Klima mesdhetare dhe toka e pasur i japin verërave tona "
            "një karakter unik. Prodhojmë Verë të Bardhë Kallmet dhe Rosé "
            "artizanale me metoda tradicionale."
        ),
        "website": "",
        "phone": "+355 69 567 8901",
        "email": "nurellari.winery@gmail.com",
    },
    {
        "owner_email": "admin@farmalb.al",
        "name": "Agriturizma Lumi i Valbonës",
        "slug": "agriturizma-lumi-valbones",
        "type": "AGRITOURISM",
        "status": "active",
        "tier": "FREE",
        "region": "Shkodra",
        "address": "Valbonë, Tropojë, Shqipëri",
        "lat": 42.4378,
        "lng": 19.8956,
        "description": (
            "Në zemër të Alpeve Shqiptare, pranë lumit të kristaltë të Valbonës, "
            "kjo agriturizmë ofron pushim të vërtetë rural. Ushqim i gatuar me "
            "produkte lokale, ecje malore guidate dhe netë të qeta nën yjet. "
            "Destinacioni ideal për dashamirësit e natyrës dhe aventurës."
        ),
        "website": "",
        "phone": "+355 68 678 9012",
        "email": "valbona.agro@gmail.com",
    },
]

# ── Experiences ────────────────────────────────────────────────────────────────
EXPERIENCES = {
    "ceren-ismet-shehu": [
        {
            "title": "Darkë Tradicionale Shqiptare",
            "type": "TASTING",
            "description": (
                "Një darkë autentike me produktet e fermës — byrek me djathë, "
                "tavë kosi, mish qengji, dhe ëmbëlsira tradicionale. "
                "Shërbyer në oborrin e shtëpisë sonë tradicionale."
            ),
            "duration_minutes": 120,
            "capacity": 20,
            "base_price": 25.00,
            "currency": "EUR",
            "status": "active",
        },
        {
            "title": "Vizitë në Fermë dhe Mëngjes Rural",
            "type": "TOUR",
            "description": (
                "Filloni ditën me një vizitë guidate nëpër fermën tonë, "
                "mësoni si prodhojmë djathin dhe mjaltin, dhe shijoni "
                "një mëngjes të pasur rural me produkte të freskëta."
            ),
            "duration_minutes": 180,
            "capacity": 12,
            "base_price": 18.00,
            "currency": "EUR",
            "status": "active",
        },
    ],
    "mrizi-i-zanave": [
        {
            "title": "Menuja Sezonale e Shefave",
            "type": "TASTING",
            "description": (
                "Pesë kurse të zgjedhura nga shefat tanë, "
                "të gjitha bazuar në produktet e ditës nga fermat lokale. "
                "Çdo pjatë tregon historinë e një ingredient shqiptar."
            ),
            "duration_minutes": 150,
            "capacity": 16,
            "base_price": 45.00,
            "currency": "EUR",
            "status": "active",
        },
        {
            "title": "Workshop Gatimi — Kuzhina Shqiptare",
            "type": "COOKING_CLASS",
            "description": (
                "Mësoni sekretet e kuzhinës tradicionale shqiptare me shefat tanë. "
                "Do të gatuajmë byrek, tavë elbasani dhe trilece, "
                "duke përdorur produkte direkt nga ferma."
            ),
            "duration_minutes": 240,
            "capacity": 10,
            "base_price": 55.00,
            "currency": "EUR",
            "status": "active",
        },
    ],
    "cantina-cobo-winery": [
        {
            "title": "Degustim Premium — Shesh i Zi",
            "type": "TASTING",
            "description": (
                "Zbuloni historinë e verës shqiptare nëpërmjet degustimit "
                "të 6 verërave tona të zgjedhura. Udhëzues profesional, "
                "djathëra artizanale dhe bukë tradicionale përfshihen."
            ),
            "duration_minutes": 90,
            "capacity": 15,
            "base_price": 35.00,
            "currency": "EUR",
            "status": "active",
        },
        {
            "title": "Tur i Vreshtit dhe Kantinës",
            "type": "TOUR",
            "description": (
                "Ecni nëpër vreshtat historike të Beratit, mësoni procesin "
                "e prodhimit të verës nga rrushi deri te shishja, "
                "dhe vizitoni bodrumet tona të lashta."
            ),
            "duration_minutes": 120,
            "capacity": 20,
            "base_price": 20.00,
            "currency": "EUR",
            "status": "active",
        },
    ],
    "ferma-organike-gomsiqe": [
        {
            "title": "Ditë në Fermë Organike",
            "type": "TOUR",
            "description": (
                "Kaloni një ditë të plotë si farmer — ushqeni kafshët, "
                "mblidhni mjaltë, vjelni fruta dhe perime. "
                "Darka me produktet e fermës suaj është përfshirë."
            ),
            "duration_minutes": 360,
            "capacity": 8,
            "base_price": 30.00,
            "currency": "EUR",
            "status": "active",
        },
    ],
    "vreshtaria-nurellari": [
        {
            "title": "Degustim Verërash Buzë Lagunës",
            "type": "TASTING",
            "description": (
                "Shijoni verërat tona artizanale me pamje nga laguna e Nartës. "
                "3 verëra të bardha dhe 1 rosé, me peshk të freskët "
                "dhe produkte lokale."
            ),
            "duration_minutes": 90,
            "capacity": 12,
            "base_price": 25.00,
            "currency": "EUR",
            "status": "active",
        },
    ],
    "agriturizma-lumi-valbones": [
        {
            "title": "Natë në Alpet Shqiptare",
            "type": "FARM_STAY",
            "description": (
                "Qëndroni një natë në kasollet tona tradicionale malore. "
                "Darka dhe mëngjesi i pasur me produkte lokale janë përfshirë. "
                "Pamje spektakolare nga malet e Valbonës."
            ),
            "duration_minutes": 1200,
            "capacity": 6,
            "base_price": 65.00,
            "currency": "EUR",
            "status": "active",
        },
        {
            "title": "Shëtitje Guidate Malore",
            "type": "TOUR",
            "description": (
                "Eksploroni shtigjet e fshehtë të Alpeve Shqiptare me guidën "
                "tonë lokale. Distanca 12km, nivel i mesëm. "
                "Drekë piknik me produkte lokale është përfshirë."
            ),
            "duration_minutes": 480,
            "capacity": 10,
            "base_price": 22.00,
            "currency": "EUR",
            "status": "active",
        },
    ],
}

# ── Products ───────────────────────────────────────────────────────────────────
PRODUCTS = {
    "ceren-ismet-shehu": [
        {
            "name": "Djathë i Bardhë Tradicional",
            "category": "CHEESE",
            "description": "Djathë i bardhë i bërë me qumësht delet tona, i kripur në shëllirë. 400g.",
            "price": 8.50,
            "currency": "EUR",
            "stock_qty": 50,
            "shippable": True,
            "weight_grams": 400,
            "status": "active",
        },
        {
            "name": "Mjaltë Mali i Lezhës",
            "category": "HONEY",
            "description": "Mjaltë natyral i bletëve tona, i mbledhur nga lulëzimi i malit. 500g.",
            "price": 12.00,
            "currency": "EUR",
            "stock_qty": 30,
            "shippable": True,
            "weight_grams": 500,
            "status": "active",
        },
    ],
    "mrizi-i-zanave": [
        {
            "name": "Byrek i Gatshëm i Ngrirë",
            "category": "OTHER",
            "description": "Byrek tradicional me djathë dhe spinaq, i gatuar në fermë, i ngrirë për transport. 1kg.",
            "price": 15.00,
            "currency": "EUR",
            "stock_qty": 20,
            "shippable": True,
            "weight_grams": 1000,
            "status": "active",
        },
        {
            "name": "Raki Kumbullë Artizanale",
            "category": "RAKIA",
            "description": "Raki e distiluar me kumbulla tona, 40°. 700ml. Prodhim i kufizuar.",
            "price": 22.00,
            "currency": "EUR",
            "stock_qty": 15,
            "shippable": True,
            "weight_grams": 900,
            "status": "active",
        },
    ],
    "cantina-cobo-winery": [
        {
            "name": "Shesh i Zi Rezerva 2020",
            "category": "WINE",
            "description": (
                "Vera jonë ikonike nga varieteti autoktone Shesh i Zi. "
                "Rubinë e thellë, tanine të buta, nota rrush të zi dhe vaniljes. "
                "750ml."
            ),
            "price": 18.00,
            "currency": "EUR",
            "stock_qty": 100,
            "shippable": True,
            "weight_grams": 1200,
            "status": "active",
        },
        {
            "name": "Kallmet i Bardhë 2022",
            "category": "WINE",
            "description": (
                "Verë e bardhë nga varieteti Kallmet, e freskët dhe aromatike. "
                "Nota limoni, lulesh të bardha dhe minerale. 750ml."
            ),
            "price": 14.00,
            "currency": "EUR",
            "stock_qty": 80,
            "shippable": True,
            "weight_grams": 1200,
            "status": "active",
        },
        {
            "name": "Koleksion Degustimi — 3 Verëra",
            "category": "WINE",
            "description": (
                "Tre shishe të zgjedhura nga koleksioni ynë: "
                "Shesh i Zi, Kallmet i Bardhë dhe Rosé. "
                "Paketim dhurate, perfekt për dashamirësit e verës."
            ),
            "price": 42.00,
            "currency": "EUR",
            "stock_qty": 25,
            "shippable": True,
            "weight_grams": 3800,
            "status": "active",
        },
    ],
    "ferma-organike-gomsiqe": [
        {
            "name": "Mjaltë Organik i Alpeve",
            "category": "HONEY",
            "description": "Mjaltë 100% organik nga bletët e Alpeve Shqiptare. I certifikuar organik. 500g.",
            "price": 14.00,
            "currency": "EUR",
            "stock_qty": 40,
            "shippable": True,
            "weight_grams": 500,
            "status": "active",
        },
        {
            "name": "Vaj Ulliri Ekstra Virgjër",
            "category": "OLIVE_OIL",
            "description": "Vaj ulliri i shtypjes së parë nga ullishtet tona 200-vjeçare. 500ml.",
            "price": 16.00,
            "currency": "EUR",
            "stock_qty": 35,
            "shippable": True,
            "weight_grams": 600,
            "status": "active",
        },
    ],
    "vreshtaria-nurellari": [
        {
            "name": "Verë e Bardhë Kallmet 2023",
            "category": "WINE",
            "description": "Verë e bardhë artizanale nga vreshtat buzë lagunës. Freskësi mesdhetare. 750ml.",
            "price": 12.00,
            "currency": "EUR",
            "stock_qty": 60,
            "shippable": True,
            "weight_grams": 1200,
            "status": "active",
        },
        {
            "name": "Rosé Nartë 2023",
            "category": "WINE",
            "description": "Verë rozë e lehtë dhe aromatike, prodhuar me metoda tradicionale. 750ml.",
            "price": 11.00,
            "currency": "EUR",
            "stock_qty": 45,
            "shippable": True,
            "weight_grams": 1200,
            "status": "active",
        },
    ],
    "agriturizma-lumi-valbones": [
        {
            "name": "Djathë Malësor i Tymosur",
            "category": "CHEESE",
            "description": "Djathë tradicional malësor i tymosur mbi dru arre. Shije unike dhe intensive. 300g.",
            "price": 10.00,
            "currency": "EUR",
            "stock_qty": 25,
            "shippable": True,
            "weight_grams": 300,
            "status": "active",
        },
        {
            "name": "Raki Rrushi Alpine",
            "category": "RAKIA",
            "description": "Raki tradicionale e distiluar dy herë, nga rrushi i maleve të Valbonës. 500ml.",
            "price": 18.00,
            "currency": "EUR",
            "stock_qty": 20,
            "shippable": True,
            "weight_grams": 700,
            "status": "active",
        },
    ],
}

# ── Promotions ─────────────────────────────────────────────────────────────────
PROMOTIONS = {
    "ceren-ismet-shehu": [
        {
            "code": "CEREN10",
            "type": "PERCENTAGE",
            "value": 10,
            "applies_to": "ALL",
            "max_uses": 50,
            "status": "active",
        },
    ],
    "cantina-cobo-winery": [
        {
            "code": "COBO15",
            "type": "PERCENTAGE",
            "value": 15,
            "applies_to": "BOOKINGS",
            "max_uses": 30,
            "status": "active",
        },
        {
            "code": "WINEPACK",
            "type": "FIXED_AMOUNT",
            "value": 5,
            "applies_to": "ORDERS",
            "max_uses": 100,
            "status": "active",
        },
    ],
    "mrizi-i-zanave": [
        {
            "code": "MRIZI20",
            "type": "PERCENTAGE",
            "value": 20,
            "applies_to": "ALL",
            "max_uses": 20,
            "status": "active",
        },
    ],
}


# ── Helpers ────────────────────────────────────────────────────────────────────
def _slugify(text):
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text


def _future(days=30, hour=10):
    safe_hour = min(hour, 22)   # never exceed 22
    return datetime.now(timezone.utc).replace(
        hour=safe_hour, minute=0, second=0, microsecond=0
    ) + timedelta(days=days)


# ── Main seed ──────────────────────────────────────────────────────────────────
def seed(db: Session) -> None:
    print("\n── Roles & Permissions ──────────────────────────────")

    role_map = {}
    for r in ROLES:
        role = db.query(Role).filter_by(code=r["code"]).first()
        if not role:
            role = Role(**r)
            db.add(role)
        role_map[r["code"]] = role
    db.flush()

    perm_map = {}
    for p in PERMISSIONS:
        perm = db.query(Permission).filter_by(code=p["code"]).first()
        if not perm:
            perm = Permission(**p)
            db.add(perm)
        perm_map[p["code"]] = perm
    db.flush()

    for role_code, perm_codes in ROLE_PERMISSIONS.items():
        role = role_map[role_code]
        existing = {rp.permission_id for rp in role.role_permissions}
        for pc in perm_codes:
            perm = perm_map[pc]
            if perm.id not in existing:
                db.add(RolePermission(role_id=role.id, permission_id=perm.id))
    db.flush()

    print("\n── Users ────────────────────────────────────────────")
    user_map = {}
    for u in USERS:
        user = db.query(User).filter_by(email=u["email"]).first()
        if not user:
            user = User(
                full_name=u["full_name"],
                email=u["email"],
                hashed_password=hash_password(u["password"]),
                status=u["status"],
                is_superuser=u["is_superuser"],
            )
            db.add(user)
            db.flush()
            db.add(UserRole(
                user_id=user.id,
                role_id=role_map[u["role_code"]].id,
            ))
            print(f"  ✓ {u['email']}  [{u['role_code']}]")
        else:
            print(f"  — {u['email']}  (exists)")
        user_map[u["email"]] = user
    db.flush()

    print("\n── Vendors ──────────────────────────────────────────")
    vendor_map = {}
    for v in VENDORS:
        vendor = db.query(Vendor).filter_by(slug=v["slug"]).first()
        if not vendor:
            owner = user_map[v["owner_email"]]
            vendor = Vendor(
                owner_id=owner.id,
                name=v["name"],
                slug=v["slug"],
                type=v["type"],
                status=v["status"],
                tier=v["tier"],
                region=v["region"],
                address=v["address"],
                lat=v["lat"],
                lng=v["lng"],
                description=v["description"],
                website=v.get("website", ""),
                phone=v.get("phone", ""),
                email=v.get("email", ""),
                approved_at=datetime.now(timezone.utc),
            )
            db.add(vendor)
            db.flush()

            # Assign VENDOR_ADMIN role scoped to this vendor
            owner_role = db.query(UserRole).filter_by(
                user_id=owner.id,
                role_id=role_map["VENDOR_ADMIN"].id,
            ).first()
            if not owner_role and not owner.is_superuser:
                db.add(UserRole(
                    user_id=owner.id,
                    role_id=role_map["VENDOR_ADMIN"].id,
                    vendor_id=vendor.id,
                    granted_at=datetime.now(timezone.utc),
                ))

            print(f"  ✓ {v['name']}  [{v['type']}] — {v['region']}")
        else:
            print(f"  — {v['name']}  (exists)")
        vendor_map[v["slug"]] = vendor
    db.flush()

    print("\n── Experiences & Slots ──────────────────────────────")
    for slug, exps in EXPERIENCES.items():
        vendor = vendor_map.get(slug)
        if not vendor:
            continue
        for e in exps:
            exists = db.query(Experience).filter_by(
                vendor_id=vendor.id, title=e["title"]
            ).first()
            if not exists:
                exp = Experience(
                    vendor_id=vendor.id,
                    title=e["title"],
                    description=e["description"],
                    type=e["type"],
                    duration_minutes=e["duration_minutes"],
                    capacity=e["capacity"],
                    base_price=e["base_price"],
                    currency=e["currency"],
                    status=e["status"],
                )
                db.add(exp)
                db.flush()

                # Add 4 upcoming slots spread over the next 2 months
                for week in [2, 3, 5, 7]:
                    start_hour = 10
                    end_hour = min(10 + (e["duration_minutes"] // 60), 22)
                    db.add(ExperienceSlot(
                        experience_id=exp.id,
                        starts_at=_future(days=week * 7, hour=start_hour),
                        ends_at=_future(days=week * 7, hour=end_hour),
                        available_spots=e["capacity"],
                        status="open",
                    ))

                print(f"  ✓ [{slug}] {e['title']}")
    db.flush()

    print("\n── Products ─────────────────────────────────────────")
    for slug, prods in PRODUCTS.items():
        vendor = vendor_map.get(slug)
        if not vendor:
            continue
        for p in prods:
            exists = db.query(Product).filter_by(
                vendor_id=vendor.id, name=p["name"]
            ).first()
            if not exists:
                db.add(Product(vendor_id=vendor.id, **p))
                print(f"  ✓ [{slug}] {p['name']}")
    db.flush()

    print("\n── Promotions ───────────────────────────────────────")
    for slug, promos in PROMOTIONS.items():
        vendor = vendor_map.get(slug)
        if not vendor:
            continue
        for p in promos:
            exists = db.query(Promotion).filter_by(
                vendor_id=vendor.id, code=p["code"]
            ).first()
            if not exists:
                db.add(Promotion(
                    vendor_id=vendor.id,
                    code=p["code"],
                    type=p["type"],
                    value=p["value"],
                    applies_to=p["applies_to"],
                    max_uses=p["max_uses"],
                    used_count=0,
                    status=p["status"],
                ))
                print(f"  ✓ [{slug}] {p['code']} — {p['type']} {p['value']}")
    db.flush()

    db.commit()
    print("\n✓ Seed complete.\n")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed(db)
    finally:
        db.close()