from tools._advisor import parse_programs

progs = parse_programs()
targets = [
    "C20100K1", "C50240CW", "A55280PT", "C55180CW",
    "C55180CW/K1", "A25800", "D25800", "A10100",
]
for t in targets:
    match = [p for p in progs if p["code"] == t]
    if match:
        print(f"{t:14s} | {match[0]['name']}")
    else:
        print(f"{t:14s} | NOT FOUND")
