import re

def validate_phone_number(phone_number: str) -> str | None:
    # Faqat raqamlarni qoldiramiz
    clean_phone = re.sub(r'\D', '', str(phone_number))

    # Agar raqam 998 bilan boshlansa va 12 ta bo'lsa
    if len(clean_phone) == 12 and clean_phone.startswith("998"):
        res = clean_phone
    # Agar 9 ta raqam bo'lsa (operator kodi bilan boshlangan)
    elif len(clean_phone) == 9:
        res = "998" + clean_phone
    else:
        return None

    # Operator kodlarini tekshirish (uzun ro'yxat)
    # 20, 33, 50, 77, 88, 90, 91, 93, 94, 95, 97, 98, 99 va h.k.
    valid_prefixes = (
        '33', '88', '90', '91', '93', '94', 
        '95', '97', '98', '99', '20', '77', '50'
    )
    
    # 998 dan keyingi 2 ta raqam prefiksga mos kelishini tekshiramiz
    if res[3:5] in valid_prefixes:
        return res
    
    return None

