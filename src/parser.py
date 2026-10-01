"""
parser.py
Module phân tích truy vấn của người dùng (Query Text) 
thành cấu trúc dữ liệu JSON Specification cho Vòng bi.
"""

import json
import re
from typing import Any, Dict, Optional


def normalize_text(text: str) -> str:
    """Chuyển văn bản về chữ thường và xóa khoảng trắng thừa."""
    return " ".join(text.lower().strip().split())


def extract_dimensions(text: str) -> Dict[str, Optional[float]]:
    if not text:
        return {"bore_d_mm": None, "outer_d_mm": None, "width_b_mm": None}

    # 1. TIỀN XỬ LÝ: Xóa hậu tố nắp chắn khi tìm kích thước (tránh dính dấu -)
    cleaned_text = re.sub(
        r'-(?:2rs[12]?|2z|zz|rs|z|llu|ddu|vv|2rsh|2rsr|2nse)\b', 
        '', 
        text, 
        flags=re.IGNORECASE
    )

    bore: Optional[float] = None
    outer: Optional[float] = None
    width: Optional[float] = None

    # 2. TRƯỜNG HỢP 3D (d x D x B)
    pattern_3d = r"\b(\d{1,3}(?:\.\d+)?)\s*(?:[xX*\-/]|\s+)\s*(\d{1,3}(?:\.\d+)?)\s*(?:[xX*\-/]|\s+)\s*(\d{1,3}(?:\.\d+)?)\b"
    m3 = re.search(pattern_3d, cleaned_text)
    if m3:
        v1, v2, v3 = float(m3.group(1)), float(m3.group(2)), float(m3.group(3))
        return {
            "bore_d_mm": min(v1, v2),
            "outer_d_mm": max(v1, v2),
            "width_b_mm": v3,
        }

    # 3. TRƯỜNG HỢP 2D (d x D)
    pattern_2d = r"\b(\d{1,3}(?:\.\d+)?)\s*(?:[xX*\-/]|\s+)\s*(\d{1,3}(?:\.\d+)?)\b"
    m2 = re.search(pattern_2d, cleaned_text)
    if m2:
        v1, v2 = float(m2.group(1)), float(m2.group(2))
        if v1 != v2:
            bore, outer = min(v1, v2), max(v1, v2)

    # 4. TRƯỜNG HỢP KÝ HIỆU d=, D=, B=
    all_d_matches = re.findall(r"\b[dD]\s*=\s*(\d{1,3}(?:\.\d+)?)", cleaned_text)
    if len(all_d_matches) >= 2:
        val1, val2 = float(all_d_matches[0]), float(all_d_matches[1])
        bore = min(val1, val2)
        outer = max(val1, val2)
    elif len(all_d_matches) == 1:
        val = float(all_d_matches[0])
        if re.search(r"\bD\s*=", cleaned_text):
            outer = val
        else:
            bore = val

    m_B = re.search(r"\b[Bb]\s*=\s*(\d{1,3}(?:\.\d+)?)", cleaned_text)
    if m_B:
        width = float(m_B.group(1))

    lower_text = cleaned_text.lower()

    # 4.1 Đường kính ngoài (D) qua chữ tiếng Việt
    if outer is None:
        m_outer = re.search(
            r"(?:od\s*=|phi\s*ngoài|phi\s*ngoai|d\s*ngoài|d\s*ngoai|ngoài|ngoai|vỏ|vo)\s*(\d{1,3}(?:\.\d+)?)",
            lower_text
        )
        if m_outer:
            outer = float(m_outer.group(1))

    # 4.2 Đường kính trong (d) qua chữ tiếng Việt
    if bore is None:
        m_bore = re.search(
            r"(?:id\s*=|phi\s*trong|d\s*trong|lỗ|lo|trục|truc|cốt|cot|\bphi(?!\s*(?:ngoài|ngoai)))\s*(\d{1,3}(?:\.\d+)?)",
            lower_text
        )
        if m_bore:
            bore = float(m_bore.group(1))

    # 4.3 Bề dày / Bề rộng (B) qua chữ tiếng Việt
    if width is None:
        m_width = re.search(
            r"(?:width\s*=|h\s*=|dày|day|bề\s*dày|be\s*day|bản\s*rộng|ban\s*rong|bề\s*rộng|bản|ban)\s*(\d{1,3}(?:\.\d+)?)",
            lower_text
        )
        if m_width:
            width = float(m_width.group(1))

    if bore and outer and bore > outer:
        bore, outer = outer, bore

    return {
        "bore_d_mm": bore,
        "outer_d_mm": outer,
        "width_b_mm": width,
    }


def extract_brand(text: str) -> Optional[str]:
    """Nhận diện thương hiệu phổ biến."""
    brands = [
        "skf", "nsk", "fag", "ntn", "koyo", "timken", 
        "nachi", "ezo", "iko", "ina", "asahi", "fyh"
    ]
    for brand in brands:
        if re.search(rf"\b{brand}\b", text, flags=re.IGNORECASE):
            return brand.upper()
    return None


def extract_bearing_type(text: str) -> Optional[str]:
    """Bóc tách CHỦNG LOẠI VÒNG BI trực tiếp từ từ khóa mô tả."""
    if not text:
        return None

    raw_text = text.lower().strip()

    if any(k in raw_text for k in ["bi côn", "bi con", "bạc đạn côn", "bac dan con", "vòng bi côn", "vong bi con", "tapered", "taper roller"]):
        return "tapered_roller"

    if any(k in raw_text for k in ["bi đũa", "bi dua", "bạc đạn đũa", "bac dan dua", "vòng bi đũa", "vong bi dua", "con lăn trụ", "cylindrical"]):
        return "cylindrical_roller"

    if any(k in raw_text for k in ["bi chà", "bi cha", "bạc đạn chà", "bac dan cha", "vòng bi chà", "vong bi cha", "bi chặn", "bi chan", "bạc đạn chặn", "bac dan chan", "thrust"]):
        return "thrust_ball"

    if any(k in raw_text for k in ["bi kim", "bạc đạn kim", "bac dan kim", "vòng bi kim", "vong bi kim", "needle roller", "needle"]):
        return "needle_roller"

    if any(k in raw_text for k in ["tự lựa", "tu lua", "bi nhào", "bi nhao", "self aligning", "self-aligning"]):
        return "self_aligning_ball"

    if any(k in raw_text for k in ["tiếp xúc góc", "tiep xuc goc", "bi xéo", "bi xeo", "angular contact"]):
        return "angular_contact_ball"

    if any(k in raw_text for k in ["carb", "hình xuyến", "hinh xuyen", "toroidal"]):
        return "carb_toroidal_roller"

    if any(k in raw_text for k in ["gối đỡ", "goi do", "vỏ gối", "insert bearing", "pillow block"]):
        return "insert_ball_bearing"

    if any(k in raw_text for k in ["bi cầu", "bi cau", "bạc đạn cầu", "bac dan cau", "rãnh sâu", "ranh sau", "deep groove"]):
        return "deep_groove_ball"

    return None


def extract_seal_type(text: str) -> Optional[str]:
    """Quy chuẩn loại nắp chắn vòng bi về 3 nhóm: seal_rubber, shield_steel, open."""
    if not text:
        return None
    
    raw_text = text.lower().strip()
    
    rubber_keywords = [
        "cao su", "nắp nhựa", "nap nhua", "phớt", "phot", "chống nước", "chong nuoc",
        "2rs", "2rs1", "2rs2", "2rsh", "2rsr", "ddu", "llu", "2rd", "2ru", "2nse", "vv", "llb",
        "rs", "rsh", "rsr", "du", "lu", "rd", "ru", "nse"
    ]
    
    steel_keywords = [
        "nắp sắt", "nap sat", "nắp thép", "nap thep", "nắp kim loại", "nap kim loai", "chắn bụi", "chan bui",
        "zz", "2z", "2zs", "2zr", "z", "zs", "zr"
    ]
    
    open_keywords = [
        "loại hở", "loai ho", "không nắp", "khong nap", "không phớt", "khong phot", 
        "hở", "trần", "tran", "open"
    ]

    tokens = set(re.split(r'[\s\-/_.,]+', raw_text))

    if any(k in raw_text for k in rubber_keywords) or any(t in tokens for t in ["2rs", "2rs1", "2rs2", "2rsh", "ddu", "llu", "vv", "llb", "2nse", "rs"]):
        return "seal_rubber"
        
    if any(k in raw_text for k in steel_keywords) or any(t in tokens for t in ["zz", "2z", "z"]):
        return "shield_steel"
        
    if any(k in raw_text for k in open_keywords):
        return "open"
        
    return None


def extract_clearance(text: str) -> Optional[str]:
    """Bóc tách khe hở hướng tâm vòng bi."""
    if not text:
        return None
        
    clean_text = text.upper()
    clean_text = re.sub(r'\bC\s+([0-5]|N)\b', r'C\1', clean_text)
    
    pattern = r'\b(C[1-5]|CN|C0)(?!\d)'
    match = re.search(pattern, clean_text)
    if match:
        result = match.group(1)
        return "CN" if result == "C0" else result
        
    return None


def extract_material(text: str) -> Optional[str]:
    """Bóc tách vật liệu của vòng bi."""
    if not text:
        return None
        
    raw_text = text.lower().strip()
    tokens = set(re.split(r'[\s\-/_.,]+', raw_text))

    vn_stainless = [
        "inox", "i-nox", "thép không gỉ", "thep khong gi", 
        "chống gỉ", "chong gi", "chống rỉ", "chong ri", "stainless"
    ]
    code_stainless_tokens = {"ss", "sus", "sus304", "sus316", "sus440c"}
    if any(k in raw_text for k in vn_stainless) or \
       any(t in code_stainless_tokens for t in tokens) or \
       any(re.match(r'^(s|w)\d{3,5}', t) for t in tokens):
        return "stainless_steel"

    vn_ceramic = ["gốm", "gom", "ceramic", "bi gốm", "bi gom"]
    code_ceramic_tokens = {"si3n4", "zro2", "ce", "hc", "cer"}
    if any(k in raw_text for k in vn_ceramic) or \
       any(t in code_ceramic_tokens for t in tokens):
        return "ceramic"

    vn_chrome = [
        "thép crom", "thep crom", "thép chrome", "thep chrome",
        "thép chịu lực", "thep chiu luc", "thép hợp kim", "thep hop kim",
        "thép tiêu chuẩn", "thep tieu chuan", "thép thường", "thep thuong",
        "thép bạc đạn", "thep bac dan", "thép vòng bi", "thep vong bi",
        "thép carbon", "thep carbon", "chrome steel", "carbon steel"
    ]
    code_chrome_tokens = {"gcr15", "52100", "100cr6", "suj2"}
    if any(k in raw_text for k in vn_chrome) or \
       any(t in code_chrome_tokens for t in tokens):
        return "chrome_steel"

    plastic_keywords = ["nhựa", "nhua", "pom", "ptfe", "peek"]
    if any(t in tokens for t in plastic_keywords):
        return "plastic"

    return None


def extract_bearing_code_info(text: str) -> Dict[str, Any]:
    """Trích xuất mã đầy đủ (part_number_raw) và mã gốc (base_part_number)."""
    if not text:
        return {
            "part_number_raw": None,
            "base_part_number": None,
            "code_digits": None,
            "inferred_bore": None,
            "bearing_type": None,
        }

    raw_text = text.upper()

    # Pattern cập nhật: Lấy toàn bộ token bao gồm cả tiền tố, phần số hiệu và hậu tố
    valid_prefix_pattern = r"(?:S|W|NU|NJ|N|HK|NA|UC|UCP|UCF|UCFL|C)?"
    pattern = (
        r"\b("
        + valid_prefix_pattern
        + r"([1-8]\d{2,4})(?:[A-Z0-9/\-]*))\b"
    )

    match = re.search(pattern, raw_text)
    if not match:
        return {
            "part_number_raw": None,
            "base_part_number": None,
            "code_digits": None,
            "inferred_bore": None,
            "bearing_type": None,
        }

    full_token = match.group(1).strip()   # VD: 608-2RS1 hoặc S608ZZ
    digits_part = match.group(2).strip()  # VD: 608

    base_part_number = digits_part
    code_digits = digits_part
    inferred_bore: Optional[int] = None
    bearing_type: Optional[str] = None

    # Suy luận chủng loại từ tiền tố và số hiệu
    first_char = code_digits[0]
    if full_token.startswith("C") and not full_token.startswith(("CN", "C0")):
        bearing_type = "carb_toroidal_roller"
    elif any(full_token.startswith(p) for p in ["NU", "NJ", "N3", "N2"]):
        bearing_type = "cylindrical_roller"
    elif any(full_token.startswith(p) for p in ["HK", "NA"]):
        bearing_type = "needle_roller"
    elif any(full_token.startswith(p) for p in ["UC", "UCP", "UCF", "UCFL"]):
        bearing_type = "insert_ball_bearing"
    elif first_char == "6":
        bearing_type = "deep_groove_ball"
    elif first_char in ["1", "2"]:
        bearing_type = "self_aligning_ball"
    elif first_char == "3":
        bearing_type = "tapered_roller"
    elif first_char == "5":
        bearing_type = "thrust_ball"
    elif first_char == "7":
        bearing_type = "angular_contact_ball"
    else:
        bearing_type = "other"

    # Tính đường kính trong d
    if first_char == "6" and len(code_digits) == 3:
        inferred_bore = int(code_digits[-1])
    elif len(code_digits) >= 4 or (full_token.startswith("C") and len(code_digits) == 3):
        last_two = int(code_digits[-2:])
        if last_two == 0:
            inferred_bore = 10
        elif last_two == 1:
            inferred_bore = 12
        elif last_two == 2:
            inferred_bore = 15
        elif last_two == 3:
            inferred_bore = 17
        else:
            inferred_bore = last_two * 5

    return {
        "part_number_raw": full_token,
        "base_part_number": base_part_number,
        "code_digits": code_digits,
        "inferred_bore": inferred_bore,
        "bearing_type": bearing_type,
    }


def parse_query(user_query: str) -> Dict[str, Any]:
    """
    Hàm chính tiếp nhận chuỗi text của người dùng 
    và trả về JSON Specification chuẩn hóa.
    """
    dims = extract_dimensions(user_query)
    normalized = normalize_text(user_query)
    code_info = extract_bearing_code_info(user_query)

    bore = dims["bore_d_mm"] if dims["bore_d_mm"] is not None else code_info["inferred_bore"]

    explicit_type = extract_bearing_type(normalized)
    final_bearing_type = explicit_type if explicit_type is not None else code_info["bearing_type"]

    spec = {
        "raw_query": user_query,
        "brand": extract_brand(normalized),
        "part_number_raw": code_info["part_number_raw"],
        "base_part_number": code_info["base_part_number"],
        "bearing_type": final_bearing_type,
        "bore_d_mm": bore,
        "outer_d_mm": dims["outer_d_mm"],
        "width_b_mm": dims["width_b_mm"],
        "seal_type": extract_seal_type(normalized),
        "clearance": extract_clearance(normalized),
        "material": extract_material(normalized),
    }

    return spec


if __name__ == "__main__":
    test_queries = [
        "608-2RS1",
        "Cần mua bạc đạn SKF 6312/C3 nắp cao su",
        "Bạc đạn S608ZZ inox",
    ]

    for q in test_queries:
        print(f"\n[Query]: {q}")
        result = parse_query(q)
        print(json.dumps(result, indent=2, ensure_ascii=False))