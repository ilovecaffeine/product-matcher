"""
tests/test_matcher.py
Bộ test tự động kiểm thử các chức năng của class ProductMatcher trong src/matcher.py
"""

import os
import pytest
import pandas as pd
from src.matcher import ProductMatcher


@pytest.fixture
def mock_csv_file(tmp_path):
    """
    Fixture tạo một file CSV tạm thời chứa dữ liệu mẫu để phục vụ kiểm thử.
    """
    csv_file = tmp_path / "test_products.csv"
    data = [
        {
            "product_id": "BRG-0001",
            "part_number": "608",
            "brand": "SKF",
            "bearing_type": "deep_groove_ball",
            "bore_d_mm": 8.0,
            "outer_d_mm": 22.0,
            "width_b_mm": 7.0,
            "seal_type": "open",
            "clearance": "CN",
            "material": "chrome_steel",
        },
        {
            "product_id": "BRG-0002",
            "part_number": "608-2RS1",
            "brand": "SKF",
            "bearing_type": "deep_groove_ball",
            "bore_d_mm": 8.0,
            "outer_d_mm": 22.0,
            "width_b_mm": 7.0,
            "seal_type": "seal_rubber",
            "clearance": "CN",
            "material": "chrome_steel",
        },
        {
            "product_id": "BRG-0003",
            "part_number": "30205",
            "brand": "KOYO",
            "bearing_type": "tapered_roller",
            "bore_d_mm": 25.0,
            "outer_d_mm": 52.0,
            "width_b_mm": 16.25,
            "seal_type": "open",
            "clearance": "CN",
            "material": "chrome_steel",
        },
        {
            "product_id": "BRG-0004",
            "part_number": "6205 C3",
            "brand": "NSK",
            "bearing_type": "deep_groove_ball",
            "bore_d_mm": 25.0,
            "outer_d_mm": 52.0,
            "width_b_mm": 15.0,
            "seal_type": "open",
            "clearance": "C3",
            "material": "chrome_steel",
        },
    ]
    df = pd.DataFrame(data)
    df.to_csv(csv_file, index=False)
    return str(csv_file)


@pytest.fixture
def matcher(mock_csv_file):
    """Fixture khởi tạo ProductMatcher với file CSV giả lập."""
    return ProductMatcher(csv_path=mock_csv_file)


class TestProductMatcher:

    def test_load_data_success(self, matcher):
        """Kiểm tra xem dữ liệu CSV có được nạp và chuẩn hóa đúng không."""
        assert not matcher.df.empty
        assert len(matcher.df) == 4
        # Kiểm tra chuẩn hóa hoa/thường
        assert matcher.df.loc[0, "brand"] == "SKF"
        assert matcher.df.loc[0, "seal_type"] == "open"

    def test_load_non_existent_file(self):
        """Kiểm tra xử lý khi đường dẫn file CSV không tồn tại."""
        invalid_matcher = ProductMatcher(csv_path="data/non_existent.csv")
        assert invalid_matcher.df.empty

    def test_calculate_score_exact_part_number(self, matcher):
        """Kiểm tra tính điểm khi khớp chính xác mã part_number_raw."""
        spec = {"part_number_raw": "608-2RS1"}
        row = matcher.df.iloc[1]  # BRG-0002
        score = matcher.calculate_score(row, spec)
        # Khớp exact mã part_number nhận 35 điểm
        assert score == 35.0

    def test_calculate_score_partial_part_number(self, matcher):
        """Kiểm tra tính điểm khi khớp một phần mã part_number_raw."""
        spec = {"part_number_raw": "608"}
        row = matcher.df.iloc[1]  # BRG-0002: 608-2RS1
        score = matcher.calculate_score(row, spec)
        # Khớp partial nhận 20 điểm
        assert score == 20.0

    def test_calculate_score_dimensions_and_type(self, matcher):
        """Kiểm tra tính điểm khớp kích thước và chủng loại."""
        spec = {
            "bore_d_mm": 25.0,
            "outer_d_mm": 52.0,
            "width_b_mm": 16.25,
            "bearing_type": "tapered_roller",
            "brand": "KOYO",
        }
        row = matcher.df.iloc[2]  # BRG-0003
        score = matcher.calculate_score(row, spec)
        # d(12) + D(9) + B(9) + bearing_type(10) + brand(10) = 50 điểm
        assert score == 50.0

    def test_match_hard_filter_bore_d(self, matcher):
        """Kiểm tra hard filter lọc sản phẩm theo đường kính trong (bore_d_mm)."""
        spec = {"bore_d_mm": 8.0}
        results = matcher.match(spec, top_k=5)

        # Chỉ các sản phẩm có bore_d_mm = 8.0 mới được trả về (BRG-0001, BRG-0002)
        assert len(results) == 2
        for item in results:
            assert item["bore_d_mm"] == 8.0

    def test_match_top_k_ranking(self, matcher):
        """Kiểm tra việc sắp xếp thứ tự ưu tiên Top K sản phẩm có điểm cao nhất."""
        spec = {
            "part_number_raw": "608-2RS1",  # Khớp exact mã BRG-0002 (35 điểm)
            "seal_type": "seal_rubber",
            "brand": "SKF",
        }
        results = matcher.match(spec, top_k=2)

        assert len(results) == 2
        # BRG-0002 khớp exact mã, seal_type và brand -> Điểm cao hơn BRG-0001
        assert results[0]["product_id"] == "BRG-0002"
        assert results[0]["match_score"] > results[1]["match_score"]

    def test_match_no_results(self, matcher):
        """Kiểm tra trường hợp không tìm thấy sản phẩm phù hợp."""
        spec = {"bore_d_mm": 999.0}  # Đường kính không tồn tại
        results = matcher.match(spec, top_k=3)
        assert results == []