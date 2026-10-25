"""Pure logic: no network, no files."""

from itertools import combinations


def find_equivocations(released: list) -> list:
    """Find two NGO-signed allocations of the same bill that add up to more than 100%.

    Args:
        released: list of Released records, each a dict with keys:
            chainId, billNo, billNullifier, ngo, donorVault, fractionBps,
            reportId, ngoSig.

    Returns:
        list of dicts, each with keys:
            billNo, billNullifier, ngo, signedTotalBps, a, b.
    """
    # Step 1: Build groups keyed by (billNullifier.lower(), ngo.lower())
    groups: dict[tuple, list] = {}
    for record in released:
        key = (record["billNullifier"].lower(), record["ngo"].lower())
        groups.setdefault(key, []).append(record)

    # Step 2-4: Check each group for equivocations
    equivocations: list[dict] = []
    for group in groups.values():
        if len(group) < 2:
            continue
        for i, j in combinations(range(len(group)), 2):
            a = group[i]
            b = group[j]

            # Step 3: Skip if they represent the same allocation
            identity_a = (
                a["donorVault"].lower(),
                a["chainId"],
                a["fractionBps"],
                a["reportId"].lower(),
            )
            identity_b = (
                b["donorVault"].lower(),
                b["chainId"],
                b["fractionBps"],
                b["reportId"].lower(),
            )
            if identity_a == identity_b:
                continue

            # Step 4: Check for equivocation
            total = a["fractionBps"] + b["fractionBps"]
            if total > 10000:
                equivocations.append({
                    "billNo": a["billNo"],
                    "billNullifier": a["billNullifier"],
                    "ngo": a["ngo"],
                    "signedTotalBps": total,
                    "a": a,
                    "b": b,
                })

    # Step 5: Sort results
    equivocations.sort(key=lambda x: (x["billNo"], x["a"]["chainId"], x["b"]["chainId"]))

    return equivocations
