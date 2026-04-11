import json
import chromadb
import os

chroma_client = chromadb.Client()
collection = None

def load_schemes():
    global collection
    with open("schemes.json", encoding="utf-8") as f:
        schemes = json.load(f)

    collection = chroma_client.get_or_create_collection("schemes")

    if collection.count() == 0:
        docs, ids, metas = [], [], []
        for i, s in enumerate(schemes):
            text = (
                f"{s['name']}. {s['description']}. "
                f"For: {', '.join(s['occupations'])}. "
                f"Caste: {', '.join(s['castes'])}. "
                f"Income below {s['income_limit']}. "
                f"Age {s['min_age']}-{s['max_age']}."
            )
            docs.append(text)
            ids.append(str(i))
            metas.append({
                "index": i,
                "name": s["name"],
                "income_limit": s["income_limit"],
                "min_age": s["min_age"],
                "max_age": s["max_age"],
                "occupations": json.dumps(s["occupations"]),
                "castes": json.dumps(s["castes"]),
                "states": json.dumps(s.get("states", ["any"])),
            })
        collection.add(documents=docs, ids=ids, metadatas=metas)
    return schemes

ALL_SCHEMES = load_schemes()

def match_schemes(age, income, occupation, caste, state="", family_size="1"):
    age = int(age)
    income = int(income)
    occupation = occupation.lower().strip()
    caste = caste.lower().strip()
    state = state.lower().strip()

    eligible = []
    for s in ALL_SCHEMES:
        if income >= s["income_limit"]:
            continue
        if age < s["min_age"] or age > s["max_age"]:
            continue
        occ_match = "any" in s["occupations"] or any(
            o.lower() in occupation or occupation in o.lower()
            for o in s["occupations"]
        )
        if not occ_match:
            continue
        caste_match = "any" in [c.lower() for c in s["castes"]] or any(
            c.lower() == caste or caste in c.lower()
            for c in s["castes"]
        )
        if not caste_match:
            continue
        state_match = "any" in [st.lower() for st in s.get("states", ["any"])] or any(
            st.lower() in state or state in st.lower()
            for st in s.get("states", ["any"])
        )
        if not state_match:
            continue
        eligible.append(s)
    return eligible

def format_schemes_for_whatsapp(schemes_list):
    lines = []
    for i, s in enumerate(schemes_list, 1):
        lines.append(
            f"{i}. {s['name']}\n"
            f"   Benefit: {s['benefit']}\n"
            f"   Documents: {s['documents']}\n"
            f"   Apply: {s.get('apply_link', 'CSC Centre')}"
        )
    return "\n\n".join(lines)