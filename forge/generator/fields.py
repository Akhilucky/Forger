from __future__ import annotations

import random
import re
import string
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any


FIRST_NAMES_MALE = [
    "James", "Robert", "John", "Michael", "David", "William", "Richard",
    "Joseph", "Thomas", "Christopher", "Daniel", "Matthew", "Anthony",
    "Mark", "Donald", "Steven", "Andrew", "Paul", "Joshua", "Kenneth",
    "Kevin", "Brian", "George", "Timothy", "Ronald", "Edward", "Jason",
    "Jeffrey", "Ryan", "Jacob", "Gary", "Nicholas", "Eric", "Jonathan",
    "Stephen", "Larry", "Justin", "Scott", "Brandon", "Benjamin",
    "Samuel", "Raymond", "Gregory", "Frank", "Alexander", "Patrick",
    "Jack", "Dennis", "Jerry", "Tyler",
]

FIRST_NAMES_FEMALE = [
    "Mary", "Patricia", "Jennifer", "Linda", "Barbara", "Elizabeth",
    "Susan", "Jessica", "Sarah", "Karen", "Lisa", "Nancy", "Betty",
    "Margaret", "Sandra", "Ashley", "Dorothy", "Kimberly", "Emily",
    "Donna", "Michelle", "Carol", "Amanda", "Melissa", "Deborah",
    "Stephanie", "Rebecca", "Sharon", "Laura", "Cynthia", "Kathleen",
    "Amy", "Angela", "Shirley", "Anna", "Brenda", "Pamela", "Emma",
    "Nicole", "Helen", "Samantha", "Katherine", "Christine", "Debra",
    "Rachel", "Carolyn", "Janet", "Catherine", "Maria", "Heather",
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
    "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez",
    "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
    "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark",
    "Ramirez", "Lewis", "Robinson", "Walker", "Young", "Allen", "King",
    "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores", "Green",
    "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell",
    "Carter", "Roberts", "Turner", "Phillips", "Evans",
]

COMPANY_PREFIXES = [
    "Tech", "Data", "Cloud", "Digital", "Smart", "Next", "Prime", "Core",
    "Global", "United", "Pacific", "Atlantic", "Meridian", "Vertex",
    "Nova", "Apex", "Pinnacle", "Summit", "Titan", "Quantum",
]

COMPANY_SUFFIXES = [
    "Systems", "Solutions", "Technologies", "Analytics", "Dynamics",
    "Innovations", "Ventures", "Group", "Partners", "Industries",
    "Labs", "Works", "Digital", "Data", "Inc", "Corp", "LLC",
]

CITIES = [
    "New York", "Los Angeles", "Chicago", "Houston", "Phoenix",
    "Philadelphia", "San Antonio", "San Diego", "Dallas", "Austin",
    "San Jose", "Jacksonville", "Fort Worth", "Columbus", "Charlotte",
    "Indianapolis", "San Francisco", "Seattle", "Denver", "Nashville",
    "Portland", "Miami", "Atlanta", "Boston", "Tampa",
]

STATES = [
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
]

COUNTRIES = [
    "United States", "Canada", "United Kingdom", "Germany", "France",
    "Australia", "Japan", "Brazil", "India", "China",
    "Italy", "Spain", "Mexico", "Netherlands", "South Korea",
    "Sweden", "Switzerland", "Singapore", "Norway", "Denmark",
]

DOMAINS = [
    "gmail.com", "outlook.com", "yahoo.com", "proton.me", "icloud.com",
    "hotmail.com", "mail.com", "hey.com", "fastmail.com", "zoho.com",
]

JOB_TITLES = [
    "Software Engineer", "Data Scientist", "Product Manager",
    "Design Engineer", "DevOps Engineer", "ML Engineer",
    "Backend Developer", "Frontend Developer", "Full Stack Developer",
    "Data Analyst", "Business Analyst", "QA Engineer",
    "Systems Architect", "Engineering Manager", "CTO",
    "VP of Engineering", "Technical Lead", "Security Engineer",
    "UX Designer", "Solutions Architect", "Research Scientist",
    "Database Administrator", "Network Engineer", "Scrum Master",
]

LOREM = [
    "lorem", "ipsum", "dolor", "sit", "amet", "consectetur",
    "adipiscing", "elit", "sed", "do", "eiusmod", "tempor",
    "incididunt", "ut", "labore", "et", "dolore", "magna", "aliqua",
]


def _name(field_hint: str | None) -> str:
    first = random.choice(FIRST_NAMES_MALE + FIRST_NAMES_FEMALE)
    last = random.choice(LAST_NAMES)
    hint = (field_hint or "").lower()
    if "first" in hint:
        return first
    if "last" in hint:
        return last
    return f"{first} {last}"


def _email() -> str:
    name = random.choice(FIRST_NAMES_MALE + FIRST_NAMES_FEMALE).lower()
    return f"{name}.{random.choice(LAST_NAMES).lower()}{random.randint(1, 99)}@{random.choice(DOMAINS)}"


def _phone() -> str:
    area = random.randint(200, 999)
    exch = random.randint(200, 999)
    line = random.randint(1000, 9999)
    return f"+1 ({area}) {exch}-{line}"


def _address() -> str:
    num = random.randint(100, 9999)
    streets = [
        "Main St", "Oak Ave", "Elm St", "Park Ave", "Broadway",
        "Maple Dr", "Cedar Ln", "Pine St", "Lake Dr", "River Rd",
        "Washington Blvd", "Lincoln Ave", "Market St", "Highland Ave",
    ]
    return f"{num} {random.choice(streets)}"


def _company() -> str:
    prefix = random.choice(COMPANY_PREFIXES)
    suffix = random.choice(COMPANY_SUFFIXES)
    if random.random() < 0.3:
        return f"{prefix}{suffix}"
    return f"{prefix} {suffix}"


def _job() -> str:
    return random.choice(JOB_TITLES)


def _date() -> str:
    start = datetime(2015, 1, 1)
    end = datetime(2026, 6, 22)
    delta = end - start
    d = start + timedelta(days=random.randint(0, delta.days))
    return d.strftime("%Y-%m-%d")


def _datetime_val() -> str:
    start = datetime(2015, 1, 1, tzinfo=timezone.utc)
    end = datetime(2026, 6, 22, tzinfo=timezone.utc)
    delta = end - start
    d = start + timedelta(seconds=random.randint(0, int(delta.total_seconds())))
    return d.isoformat()


def _category(existing: list[str] | None = None) -> str:
    cats = existing or [
        "Active", "Inactive", "Pending", "Suspended", "Archived",
        "Gold", "Silver", "Bronze", "Platinum", "Basic",
        "Premium", "Enterprise", "Pro", "Free", "Trial",
        "North", "South", "East", "West", "Central",
        "A", "B", "C", "D", "F",
        "High", "Medium", "Low", "Critical",
        "New", "Returning", "VIP", "Blocked",
    ]
    return random.choice(cats)


def _paragraph(min_words: int = 10, max_words: int = 40) -> str:
    n = random.randint(min_words, max_words)
    return " ".join(random.choice(LOREM) for _ in range(n)).capitalize() + "."


def _url() -> str:
    names = ["example", "demo", "test", "app", "api", "data", "forge", "hub", "portal", "platform"]
    tlds = [".com", ".io", ".org", ".net", ".dev", ".app", ".ai"]
    return f"https://www.{random.choice(names)}{random.choice(tlds)}/{random.choice(string.ascii_lowercase)}{random.randint(1,999)}"


def _numeric(mu: float | None = None, sigma: float | None = None,
             min_v: float = 0, max_v: float = 1000) -> float:
    if mu is not None and sigma is not None:
        return max(min_v, min(max_v, random.gauss(mu, sigma)))
    return random.uniform(min_v, max_v)


def _integer(mu: float | None = None, sigma: float | None = None,
             min_v: int = 0, max_v: int = 1000) -> int:
    return round(_numeric(mu, sigma, min_v, max_v))


def generate(pattern: dict | None, hint: str | None,
             distribution: dict | None, field_name: str) -> Any:
    if distribution and distribution.get("kind") == "categorical":
        cats = list(distribution["categories"].keys())
        probs = list(distribution["categories"].values())
        return random.choices(cats, weights=probs, k=1)[0]

    if pattern and pattern.get("parts"):
        return _from_pattern(pattern["parts"])

    hint_lower = (hint or "").lower()
    if "email" in hint_lower or "mail" in hint_lower:
        return _email()
    if "phone" in hint_lower or "mobile" in hint_lower or "phone" in field_name.lower():
        return _phone()
    if "address" in hint_lower or "street" in hint_lower:
        return _address()
    if "city" in hint_lower or "town" in hint_lower:
        return random.choice(CITIES)
    if "state" in hint_lower or "province" in hint_lower:
        return random.choice(STATES)
    if "country" in hint_lower or "nation" in hint_lower:
        return random.choice(COUNTRIES)
    if "zip" in hint_lower or "postal" in hint_lower or "pincode" in hint_lower:
        return f"{random.randint(10000, 99999)}"
    if "company" in hint_lower or "organization" in hint_lower or "employer" in hint_lower:
        return _company()
    if "job" in hint_lower or "title" in hint_lower or "position" in hint_lower or "role" in hint_lower:
        return _job()
    if "name" in hint_lower or ("first" in field_name.lower() and "name" in field_name.lower()):
        return _name(hint)
    if "first" in field_name.lower():
        return _name(hint)
    if "last" in field_name.lower():
        return _name(hint)
    if "url" in hint_lower or "website" in hint_lower or "link" in hint_lower:
        return _url()
    if "price" in hint_lower or "cost" in hint_lower or "amount" in hint_lower or "salary" in hint_lower:
        return round(_numeric(min_v=0, max_v=500000), 2)
    if "age" in hint_lower:
        return random.randint(18, 80)
    if "id" in hint_lower or "uuid" in hint_lower or "guid" in hint_lower:
        return str(uuid.uuid4())
    if "gender" in hint_lower or "sex" in hint_lower:
        return random.choice(["Male", "Female", "Non-binary"])
    if "category" in hint_lower or "type" in hint_lower or "status" in hint_lower:
        return _category()
    if "description" in hint_lower or "comment" in hint_lower or "note" in hint_lower or "text" in hint_lower or "content" in hint_lower:
        return _paragraph()
    if "date" in hint_lower or "birth" in hint_lower or "dob" in hint_lower:
        return _date()
    if "timestamp" in hint_lower or "created" in hint_lower or "updated" in hint_lower:
        return _datetime_val()

    if distribution:
        kind = distribution.get("kind")
        if kind == "normal":
            mu = distribution.get("mu", 0)
            sigma = distribution.get("sigma", 1)
            min_v = distribution.get("min", 0)
            max_v = distribution.get("max", 1000)
            return _integer(mu=mu, sigma=sigma, min_v=int(min_v), max_v=int(max_v))
        return _integer(min_v=int(distribution.get("min", 0)), max_v=int(distribution.get("max", 1000)))

    return _integer()


def _from_pattern(parts: list) -> str:
    result = []
    for kind, val in parts:
        if kind == "alpha_upper":
            result.append("".join(random.choice(string.ascii_uppercase) for _ in range(val)))
        elif kind == "alpha_title":
            result.append(random.choice(string.ascii_uppercase) + "".join(random.choice(string.ascii_lowercase) for _ in range(val - 1)))
        elif kind == "alpha_lower":
            result.append("".join(random.choice(string.ascii_lowercase) for _ in range(val)))
        elif kind == "digit":
            result.append("".join(random.choice(string.digits) for _ in range(val)))
        elif kind == "literal":
            result.append(val)
    return "".join(result)
