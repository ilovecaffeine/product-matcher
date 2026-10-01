# Bearing Search System (Hệ thống Tìm kiếm Vòng bi / Bạc đạn)

Hệ thống hỗ trợ bóc tách thông số kỹ thuật vòng bi từ câu truy vấn tự nhiên (Natural Language Query) và thực hiện tìm kiếm, xếp hạng sản phẩm phù hợp nhất trong cơ sở dữ liệu catalogue CSV.

---

## Tính năng chính

- **NLP Query Parser (`src/parser.py`)**: 
  - Bóc tách tự động kích thước hình học 2D/3D ($d \times D \times B$), bắt các ký hiệu viết tắt (`d=25`, `D=52`, `B=15`, `phi 25`, `lỗ 25`, `ngoài 52`...).
  - Nhận diện chủng loại vòng bi (`bearing_type`): Ưu tiên loại được chỉ định trực tiếp từ khóa (*bi côn, bi đũa, bi chà, bi tự lựa...*), sau đó tự suy luận theo chuẩn mã số ISO (*6312 $\rightarrow$ deep_groove_ball, 30205 $\rightarrow$ tapered_roller*).
  - Trích xuất thương hiệu (*SKF, NSK, KOYO, FAG, NTN...*), nắp phớt (*2RS, ZZ, open*), khe hở (*C2, C3, CN*), và vật liệu (*inox, gốm, thép crom*).
- **Smart Matcher (`src/matcher.py`)**: 
  - Cơ chế lọc cứng (Hard Filter) theo đường kính trục ($d$).
  - Thuật toán chấm điểm độ tương đồng đa tiêu chí (Mã sản phẩm, Kích thước, Chủng loại, Thương hiệu, Nắp phớt, Khe hở nhiệt, Vật liệu).
- **Giao diện dòng lệnh CLI (`main.py`)**: 
  - Chạy tương tác trực tiếp trên Terminal, hỗ trợ tìm kiếm liên tục nhiều câu truy vấn.

---

## Cấu trúc thư mục

```text
product-matcher/
│
├── data/
│   ├── products.csv       # Cơ sở dữ liệu sản phẩm đã chuẩn hóa
│   └── sources.md         # Nguồn tài liệu và catalogue tham khảo
│
├── src/
│   ├── main.py            # Giao diện CLI và điều phối pipeline
│   ├── parser.py          # Bóc tách Text tự nhiên -> JSON Specification
│   └── matcher.py         # Thuật toán chấm điểm và xếp hạng sản phẩm
│
├── tests/
│   └── test_matcher.py    # Unit test kiểm thử logic matching
│
├── requirements.txt       # Danh sách thư viện phụ thuộc (pandas, pytest...)
└── README.md              # Tài liệu hướng dẫn sử dụng
```

---

## Cài đặt & Chuẩn bị

### 1. Yêu cầu môi trường
* **Python 3.8+**

### 2. Cài đặt thư viện

Cài đặt các thư viện cần thiết thông qua file `requirements.txt`:

```bash
pip install -r requirements.txt
```

---

## Hướng dẫn sử dụng

Khởi chạy chương trình tìm kiếm tương tác:

```bash
python -m src.main
```

### Minh họa chạy thực tế trên Terminal:

```text
==========================================
      HỆ THỐNG TÌM KIẾM SẢN PHẨM VÒNG BI
==========================================
Hướng dẫn:
 - Nhập câu truy vấn (ví dụ: 'Vòng bi 6312-2RS', 'bạc đạn d=25 D=52') và nhấn Enter.
 - Nhập 'esc', 'exit', hoặc 'quit' để thoát chương trình.

Enter query: bạc đạn côn d=25 KOYO

==========================================
QUERY: 'bạc đạn côn d=25 KOYO'
PARSED SPEC:
{
  "raw_query": "bạc đạn côn d=25 KOYO",
  "brand": "KOYO",
  "part_number_raw": null,
  "bearing_type": "tapered_roller",
  "bore_d_mm": 25.0,
  "outer_d_mm": null,
  "width_b_mm": null,
  "seal_type": null,
  "clearance": null,
  "material": null
}

TOP RESULTS FROM 'data/products.csv':
 1. [32.0 pts] ID: BRG-0086 | Brand: KOYO | Type: tapered_roller | Name: 30205
 2. [22.0 pts] ID: BRG-0054 | Brand: KOYO | Type: deep_groove_ball | Name: 6205-2RS
 3. [22.0 pts] ID: BRG-0022 | Brand: KOYO | Type: deep_groove_ball | Name: 6005-2RS
==========================================
```

---

## Định dạng dữ liệu chuẩn (`data/products.csv`)

Cơ sở dữ liệu sản phẩm bao gồm các trường thông số kỹ thuật chuẩn quốc tế:

| Cột dữ liệu | Kiểu | Mô tả | Ví dụ |
| :--- | :--- | :--- | :--- |
| `product_id` | String | Mã định danh nội bộ | `BRG-0086` |
| `part_number` | String | Mã vòng bi đầy đủ | `30205`, `6205-2RS` |
| `brand` | String | Hãng sản xuất | `KOYO`, `SKF`, `NSK` |
| `bearing_type` | String | Chủng loại vòng bi | `tapered_roller`, `deep_groove_ball` |
| `bore_d_mm` | Float | Đường kính trong ($d$) | `25.0` |
| `outer_d_mm` | Float | Đường kính ngoài ($D$) | `52.0` |
| `width_b_mm` | Float | Độ dày / Bề rộng ($B$) | `16.25` |
| `seal_type` | String | Loại nắp chắn | `open`, `seal_rubber`, `shield_steel` |
| `clearance` | String | Khe hở hướng tâm | `CN`, `C2`, `C3` |
| `material` | String | Vật liệu chế tạo | `chrome_steel`, `stainless_steel` |
| `dynamic_load_cr_kn` | Float | Tải trọng động danh định ($C_r$) | `35.2` |
| `static_load_cor_kn` | Float | Tải trọng tĩnh danh định ($C_{0r}$) | `34.0` |
| `limiting_speed_rpm` | Int | Tốc độ vòng quay tối đa | `10000` |

---