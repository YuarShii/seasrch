// CẤU HÌNH API
const API_URL = "http://127.0.0.1:8000/api";

// TRẠNG THÁI HIỆN TẠI (STATE)
let currentState = {
  tu_khoa: "",
  gia_min: null,
  gia_max: null,
  danh_muc: null,
  sao_toi_thieu: null,
  sap_xep: 0, // 0: Mới nhất
  page: 1,
  page_size: 12,
};

// --- HÀM KHỞI TẠO ---
async function init() {
  await loadCategories();
  await fetchProducts();
}

// --- 1. LẤY DANH MỤC TỪ API ---
async function loadCategories() {
  try {
    const res = await fetch(`${API_URL}/danh-muc`);
    const data = await res.json();
    const list = document.getElementById("categoryList");

    // Reset list và thêm nút "Tất cả"
    list.innerHTML = `<li class="category-item ${
      currentState.danh_muc === null ? "active" : ""
    }" onclick="applyCategory(null, this)">Tất cả</li>`;

    if (data.data) {
      data.data.forEach((cat) => {
        list.innerHTML += `<li class="category-item" onclick="applyCategory('${cat}', this)">${cat}</li>`;
      });
    }
  } catch (e) {
    console.error("Lỗi tải danh mục:", e);
  }
}

// --- 2. GỌI API TÌM KIẾM SẢN PHẨM ---
async function fetchProducts() {
  document.getElementById("loading").style.display = "block";
  document.getElementById("productGrid").innerHTML = "";

  try {
    // Xây dựng URL Query String
    let url = new URL(`${API_URL}/san-pham/tim-kiem`);
    if (currentState.tu_khoa)
      url.searchParams.append("tu_khoa", currentState.tu_khoa);
    if (currentState.gia_min)
      url.searchParams.append("gia_min", currentState.gia_min);
    if (currentState.gia_max)
      url.searchParams.append("gia_max", currentState.gia_max);
    if (currentState.danh_muc)
      url.searchParams.append("danh_muc", currentState.danh_muc);
    if (currentState.sao_toi_thieu)
      url.searchParams.append("sao_toi_thieu", currentState.sao_toi_thieu);
    url.searchParams.append("sap_xep", currentState.sap_xep);
    url.searchParams.append("page", currentState.page);
    url.searchParams.append("page_size", currentState.page_size);

    const res = await fetch(url);
    const products = await res.json();

    renderProducts(products);
  } catch (e) {
    console.error("Lỗi tải sản phẩm:", e);
    document.getElementById("productGrid").innerHTML =
      '<p style="padding:20px">Không tải được dữ liệu (Check API)</p>';
  } finally {
    document.getElementById("loading").style.display = "none";
    updatePaginationUI();
  }
}

// --- 3. RENDER GIAO DIỆN SẢN PHẨM ---
function renderProducts(products) {
  const grid = document.getElementById("productGrid");

  if (products.length === 0) {
    grid.innerHTML =
      '<p style="grid-column: 1/-1; text-align:center; padding: 20px;">Không tìm thấy sản phẩm nào.</p>';
    return;
  }

  products.forEach((p) => {
    // Tạo icon placeholder ngẫu nhiên
    const icon = p.tenDanhMuc.includes("Điện")
      ? "fa-mobile-alt"
      : p.tenDanhMuc.includes("Thời")
      ? "fa-tshirt"
      : "fa-box";

    // Định dạng tiền tệ
    const price = new Intl.NumberFormat("vi-VN", {
      style: "currency",
      currency: "VND",
    }).format(p.giaBan);

    // Render thẻ HTML
    const html = `
                <div class="product-card">
                    <div class="product-img">
                        <div class="img-placeholder">
                            <i class="fas ${icon}" style="font-size: 30px; margin-bottom: 5px;"></i>
                            <span style="font-size: 10px;">SHOP DEMO</span>
                        </div>
                        ${
                          p.phanTramGiamGia > 0
                            ? `<div style="position:absolute; top:0; right:0; background:#f63; color:white; font-size:10px; padding:2px 4px;">-${Math.round(
                                p.phanTramGiamGia
                              )}%</div>`
                            : ""
                        }
                    </div>
                    <div class="product-info">
                        <div class="product-name">${p.tenSanPham}</div>
                        <div class="product-tags">
                            <span class="tag-mall">Mall</span>
                        </div>
                        <div class="product-price-row">
                            <span class="price-current">${price}</span>
                        </div>
                        <div class="product-meta">
                            <div class="rating">
                                ${renderStars(p.diemDanhGiaTB)}
                            </div>
                            <div>Đã bán ${
                              p.soLuongCon > 0 ? "nhiều" : "hết"
                            }</div>
                        </div>
                        <div class="product-meta" style="margin-top:5px; font-size:9px;">
                            ${p.tenCuaHang}
                        </div>
                    </div>
                </div>
                `;
    grid.innerHTML += html;
  });
}

function renderStars(rating) {
  if (!rating) return "";
  let html = '<span class="stars-small">';
  for (let i = 1; i <= 5; i++) {
    if (i <= rating) html += '<i class="fas fa-star"></i>';
    else html += '<i class="far fa-star"></i>';
  }
  html += `</span>`;
  return html;
}

// --- CÁC HÀM XỬ LÝ SỰ KIỆN (FILTERS) ---

function applySearch() {
  currentState.tu_khoa = document.getElementById("searchInput").value;
  currentState.page = 1;
  fetchProducts();
}

function applyCategory(catName, element) {
  // Update Active UI
  document
    .querySelectorAll(".category-item")
    .forEach((el) => el.classList.remove("active"));
  element.classList.add("active");

  currentState.danh_muc = catName;
  currentState.page = 1;
  fetchProducts();
}

function applyPrice() {
  const min = document.getElementById("priceMin").value;
  const max = document.getElementById("priceMax").value;
  currentState.gia_min = min ? parseFloat(min) : null;
  currentState.gia_max = max ? parseFloat(max) : null;
  currentState.page = 1;
  fetchProducts();
}

function applyRating(stars) {
  currentState.sao_toi_thieu = stars;
  currentState.page = 1;
  fetchProducts();
}

function applySort(sortValue, btnElement) {
  document
    .querySelectorAll(".sort-btn")
    .forEach((el) => el.classList.remove("active"));
  btnElement.classList.add("active");

  currentState.sap_xep = sortValue;
  currentState.page = 1;
  fetchProducts();
}

function downloadCSV() {
  const keyword = document.getElementById("searchInput").value; // ID ô tìm kiếm
  const minPrice = document.getElementById("priceMin").value; // ID ô giá thấp nhất
  const maxPrice = document.getElementById("priceMax").value; // ID ô giá cao nhất
  const category = currentState ? currentState.danh_muc : null;
  const rating = currentState ? currentState.sao_toi_thieu : null;
  const sort = currentState ? currentState.sap_xep : 0;

  let url = `http://127.0.0.1:8000/api/products/export?`;

  let params = [];
  if (keyword) params.push(`keyword=${encodeURIComponent(keyword)}`);
  if (minPrice) params.push(`min_price=${minPrice}`);
  if (maxPrice) params.push(`max_price=${maxPrice}`);
  if (category) params.push(`category=${encodeURIComponent(category)}`);
  if (rating) params.push(`min_rating=${rating}`);
  params.push(`sort_by=${sort}`);

  url += params.join("&");

  console.log("Đang tải CSV từ:", url);
  window.open(url, "_blank");
}

function changePage(delta) {
  if (currentState.page + delta < 1) return;
  currentState.page += delta;
  fetchProducts();
}

function updatePaginationUI() {
  document.getElementById("pageInfo").innerText = `Trang ${currentState.page}`;
}

function resetFilters() {
  currentState = {
    ...currentState,
    page: 1,
    danh_muc: null,
    tu_khoa: "",
  };
  loadCategories(); // Reset UI danh mục
  fetchProducts();
}

// Enter search
document
  .getElementById("searchInput")
  .addEventListener("keypress", function (event) {
    if (event.key === "Enter") applySearch();
  });

// CHẠY APP
init();
