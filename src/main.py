"""
main.py
Ứng dụng CLI tìm kiếm sản phẩm vòng bi/bạc đạn dựa trên Parser và Matcher.
python -m src.main
"""

import json
import sys
from src.parser import parse_query
from src.matcher import ProductMatcher


def main():
    # Khởi tạo matcher
    matcher = ProductMatcher(csv_path="data/products.csv")

    print("==========================================")
    print("      HỆ THỐNG TÌM KIẾM SẢN PHẨM VÒNG BI   ")
    print("==========================================")
    print("Hướng dẫn:")
    print(" - Nhập câu truy vấn (ví dụ: 'Vòng bi 6312-2RS', 'bạc đạn d=25 D=52') và nhấn Enter.")
    print(" - Nhập 'esc', 'exit', hoặc 'quit' để thoát chương trình.\n")

    while True:
        try:
            # Nhận query từ người dùng
            query = input("Enter query: ").strip()

            # Kiểm tra lệnh thoát
            if not query or query.lower() in ["esc", "exit", "quit"]:
                print("\nĐã thoát chương trình.")
                break

            # 1. Bóc tách query thành JSON Spec
            spec = parse_query(query)

            # 2. Match sản phẩm từ CSV
            results = matcher.match(spec, top_k=3)

            # 3. In kết quả chuẩn format
            print(f"\n==========================================")
            print(f"QUERY: '{query}'")
            print(f"PARSED SPEC:\n{json.dumps(spec, indent=2, ensure_ascii=False)}")
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

            print("==========================================\n")

        except KeyboardInterrupt:
            # Xử lý khi nhấn Ctrl+C
            print("\n\nĐã thoát chương trình.")
            sys.exit(0)
        except Exception as e:
            print(f"\n[ERROR] Đã xảy ra lỗi: {e}\n")


if __name__ == "__main__":
    main()