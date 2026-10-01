"""
src/matcher.py
Module nhận JSON Specification từ src/parser.py 
và tìm kiếm top N sản phẩm phù hợp nhất trong data/products.csv.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional


class ProductMatcher:
    def __init__(self, csv_path: str = "data/products.csv"):
        """
        Khởi tạo matcher và nạp dữ liệu từ CSV.
        """
        self.csv_path = csv_path
        self.df = self._load_data()

    def _load_data(self) -> pd.DataFrame:
        """Đọc và chuẩn hóa dữ liệu từ file CSV."""
        try:
            df = pd.read_csv(self.csv_path)
            
            # Chuẩn hóa các cột văn bản (bao gồm bearing_type)
            string_cols = ["part_number", "brand", "bearing_type", "seal_type", "clearance", "material"]
            for col in string_cols:
                if col in df.columns:
                    df[col] = df[col].fillna("").astype(str).str.strip()
                    if col in ["part_number", "brand", "clearance"]:
                        df[col] = df[col].str.upper()
                    else:
                        df[col] = df[col].str.lower()

            # Chuẩn hóa các cột kích thước số
            dim_cols = ["bore_d_mm", "outer_d_mm", "width_b_mm"]
            for col in dim_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce")

            return df
        except FileNotFoundError:
            print(f"[ERROR] Không tìm thấy file dữ liệu tại '{self.csv_path}'")
            return pd.DataFrame()

    def calculate_score(self, row: pd.Series, spec: Dict[str, Any]) -> float:
        """
        Thang điểm tương đồng (Tổng tối đa: 100 điểm)
        - Part Number (Mã số): 35 điểm
        - Kích thước (d x D x B): 30 điểm
        - Loại vòng bi (Bearing Type): 10 điểm
        - Thương hiệu (Brand): 10 điểm
        - Thuộc tính phụ (Seal, Clearance, Material): 15 điểm (Mỗi thuộc tính 5 điểm)
        """
        score = 0.0

	   # 1. Khớp mã vòng bi (35 điểm)
        req_part = spec.get("part_number_raw")
        req_base_part = spec.get("base_part_number") or req_part

        if "part_number" in row and pd.notna(row["part_number"]):
            row_part = str(row["part_number"]).upper()
            req_part_str = str(req_part).upper() if req_part else ""
            req_base_str = str(req_base_part).upper() if req_base_part else ""

            # Nếu khớp chính xác mã đầy đủ trong CSV
            if req_part_str and row_part == req_part_str:
                score += 35.0
            # Nếu khớp mã cơ sở (VD: 608) với phần đầu của mã trong CSV
            elif req_base_str and (row_part == req_base_str or row_part.startswith(req_base_str)):
                score += 30.0
            elif req_part_str in row_part or row_part in req_part_str:
                score += 20.0

        # 2. Khớp kích thước (30 điểm)
        req_d = spec.get("bore_d_mm")
        req_D = spec.get("outer_d_mm")
        req_B = spec.get("width_b_mm")

        # Đường kính trong d (12 điểm)
        if req_d is not None and "bore_d_mm" in row and pd.notna(row["bore_d_mm"]):
            if abs(row["bore_d_mm"] - req_d) < 0.1:
                score += 12.0

        # Đường kính ngoài D (9 điểm)
        if req_D is not None and "outer_d_mm" in row and pd.notna(row["outer_d_mm"]):
            if abs(row["outer_d_mm"] - req_D) < 0.1:
                score += 9.0

        # Bề dày B (9 điểm)
        if req_B is not None and "width_b_mm" in row and pd.notna(row["width_b_mm"]):
            if abs(row["width_b_mm"] - req_B) < 0.1:
                score += 9.0

        # 3. Khớp chủng loại / loại vòng bi (10 điểm)
        req_type = spec.get("bearing_type")
        if req_type and "bearing_type" in row and pd.notna(row["bearing_type"]):
            if str(row["bearing_type"]).lower() == str(req_type).lower():
                score += 10.0

        # 4. Khớp thương hiệu (10 điểm)
        req_brand = spec.get("brand")
        if req_brand and "brand" in row and pd.notna(row["brand"]):
            if str(row["brand"]).upper() == str(req_brand).upper():
                score += 10.0

        # 5. Thuộc tính phụ (15 điểm)
        # Nắp phớt (5 điểm)
        req_seal = spec.get("seal_type")
        if req_seal and "seal_type" in row and pd.notna(row["seal_type"]):
            if str(row["seal_type"]).lower() == str(req_seal).lower():
                score += 5.0

        # Khe hở (5 điểm)
        req_clearance = spec.get("clearance")
        if req_clearance and "clearance" in row and pd.notna(row["clearance"]):
            if str(row["clearance"]).upper() == str(req_clearance).upper():
                score += 5.0

        # Vật liệu (5 điểm)
        req_mat = spec.get("material")
        if req_mat and "material" in row and pd.notna(row["material"]):
            if str(row["material"]).lower() == str(req_mat).lower():
                score += 5.0

        return score

    def match(self, spec: Dict[str, Any], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Thực hiện lọc và tìm top K sản phẩm phù hợp nhất.
        """
        if self.df.empty:
            return []

        candidates = self.df.copy()

        # Hard Filter: Lọc theo bore_d_mm nếu người dùng có yêu cầu rõ ràng
        req_d = spec.get("bore_d_mm")
        if req_d is not None and "bore_d_mm" in candidates.columns:
            valid_mask = candidates["bore_d_mm"].isna() | (abs(candidates["bore_d_mm"] - req_d) <= 0.5)
            filtered = candidates[valid_mask]
            if not filtered.empty:
                candidates = filtered

        # Chấm điểm
        candidates["match_score"] = candidates.apply(lambda row: self.calculate_score(row, spec), axis=1)

        # Bỏ sản phẩm 0 điểm
        matched = candidates[candidates["match_score"] > 0].copy()
        if matched.empty:
            return []

        # Xếp hạng & lấy Top K
        matched = matched.sort_values(by="match_score", ascending=False)
        top_results = matched.head(top_k)

        # Replace NaN bằng None trước khi serialize JSON
        top_results = top_results.replace({np.nan: None})

        return top_results.to_dict(orient="records")


# ==========================================
# KHỐI THỰC THI CHÍNH (TEST TRỰC TIẾP FILE CSV)
# ==========================================
if __name__ == "__main__":
    import json
    from parser import parse_query

    # Khởi tạo matcher trỏ tới file data/products.csv thực
    matcher = ProductMatcher(csv_path="data/products.csv")

    test_queries = [
        "Vòng bi 6312-2RS",
        "bạc đạn d=25 D=52 B=15",
        "vòng bi SKF 6205 C3",
        "bạc đạn côn d=25"
    ]

    for q in test_queries:
        print(f"\n==========================================")
        print(f"QUERY: '{q}'")
        
        # 1. Bóc tách query thành JSON Spec
        spec = parse_query(q)
        print(f"PARSED SPEC:\n{json.dumps(spec, indent=2, ensure_ascii=False)}")
        
        # 2. Match sản phẩm trong CSV
        results = matcher.match(spec, top_k=3)
        print(f"\nTOP RESULTS FROM 'data/products.csv':")
        if not results:
            print(" Không tìm thấy sản phẩm phù hợp.")
        else:
            for i, res in enumerate(results, 1):
                p_id = res.get("product_id", "N/A")
                score = res.get("match_score", 0)
                name = res.get("name") or res.get("part_number") or "N/A"
                brand = res.get("brand", "N/A")
                b_type = res.get("bearing_type", "N/A")
                print(f" {i}. [{score} pts] ID: {p_id} | Brand: {brand} | Type: {b_type} | Name: {name}")