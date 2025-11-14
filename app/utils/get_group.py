from typing import Dict, FrozenSet
from config import GROUPS

# Hudud kategoriyalari
TOSHKENT = {"Toshkent shahri", "Toshkent viloyati"}
VODIY = {"Andijon"}

# Viloyat → token
REGION_TOKEN: Dict[str, str] = {
    "Toshkent shahri": "toshkentsh",
    "Toshkent viloyati": "toshkentvil",
    "Andijon": "andijon",
}

CATEGORY_BY_VIL: Dict[str, str] = (
    {vil: "toshkent" for vil in TOSHKENT} |
    {vil: "vodiy" for vil in VODIY}
)

# Maxsus token juftliklar (Toshkentli)
PAIR_TO_GROUP: Dict[FrozenSet[str], int] = {
    frozenset(k.split("_")): v for k, v in GROUPS.items() if "_" in k
}

# Asosiy funksiya
async def get_group_id(from_vil: str, to_vil: str) -> int:
    try:
        token1 = REGION_TOKEN[from_vil]
        token2 = REGION_TOKEN[to_vil]
    except KeyError as e:
        raise ValueError(f"❌ Noto‘g‘ri viloyat nomi: {e.args[0]}")

    # 🔁 Toshkentni yagona tokenga tushiramiz
    if token1 in {"toshkentsh", "toshkentvil"}:
        token1 = "toshkent"
    if token2 in {"toshkentsh", "toshkentvil"}:
        token2 = "toshkent"

    pair_key = frozenset({token1, token2})
    if pair_key in PAIR_TO_GROUP:
        return PAIR_TO_GROUP[pair_key]

    # Toifaviy kombinatsiya
    cat1 = CATEGORY_BY_VIL.get(from_vil)
    cat2 = CATEGORY_BY_VIL.get(to_vil)

    if cat1 is None or cat2 is None:
        raise ValueError(f"❌ Toifa aniqlanmadi: {from_vil=} {to_vil=}")


    raise ValueError(f"❌ Guruh topilmadi: {from_vil} → {to_vil}")