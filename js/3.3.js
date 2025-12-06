// --- 1. CHUYỂN TAB ---
function switchTab(tabId, el) {
  document
    .querySelectorAll(".tab-panel")
    .forEach((tab) => tab.classList.remove("active"));
  document
    .querySelectorAll(".menu-item")
    .forEach((item) => item.classList.remove("active"));
  document.getElementById(tabId).classList.add("active");
  el.classList.add("active");
}

// ==============================
// 2. FETCH DOANH THU
// ==============================
let revChartInstance = null;

async function renderChart() {
  const month = document.getElementById("monthSelect").value;
  const year = document.querySelector('input[type="number"]').value;

  const res = await fetch(
    `http://localhost:8000/analytics/revenue?month=${month}&year=${year}`
  );
  const apiData = await res.json();

  const ctx = document.getElementById("revenueChart").getContext("2d");

  if (revChartInstance) revChartInstance.destroy();

  revChartInstance = new Chart(ctx, {
    type: "bar",
    data: {
      labels: apiData.labels,
      datasets: [
        {
          label: "Doanh Thu (Triệu VNĐ)",
          data: apiData.values,
          backgroundColor: "#ee4d2d",
          barThickness: 50,
          borderRadius: 4,
        },
      ],
    },
    options: { responsive: true, maintainAspectRatio: false },
  });
}

// ==============================
// 3. FETCH ĐƠN HÀNG
// ==============================
async function checkOrder() {
  const id = document.getElementById("orderInput").value;
  const box = document.getElementById("orderResult");

  if (!id) return alert("Vui lòng nhập mã đơn!");
  box.style.display = "block";

  const res = await fetch(`http://localhost:8000/orders/${id}`);
  const data = await res.json();

  document.getElementById("stt-status").innerHTML = data.success
    ? `<span style="color:#26aa99"><i class="fas fa-check-circle"></i> Đã Giao Hàng</span>`
    : `<span style="color:#ee4d2d"><i class="fas fa-times-circle"></i> ${data.status}</span>`;

  document.getElementById("stt-sub").innerText = data.subtotal + " ₫";
  document.getElementById("stt-disc").innerText = "- " + data.discount + " ₫";
  document.getElementById("stt-final").innerText = data.final + " ₫";
}

// ==============================
// 4. FETCH SHIPPER
// ==============================
async function initShipper() {
  const res = await fetch("http://localhost:8000/shippers");
  const shippers = await res.json();

  const tbody = document.getElementById("shipperListBody");
  tbody.innerHTML = "";

  shippers.forEach((s) => {
    let stars = "";
    for (let i = 1; i <= 5; i++)
      stars +=
        i <= Math.round(s.score)
          ? '<i class="fas fa-star"></i>'
          : '<i class="far fa-star"></i>';

    let rank =
      s.score >= 4.5
        ? '<span style="color:#26aa99;font-weight:bold;">Xuất Sắc</span>'
        : '<span style="color:#f6a700;">Khá</span>';

    tbody.innerHTML += `
                <tr>
                    <td>#${s.id}</td>
                    <td><strong>${s.name}</strong></td>
                    <td><span class="stars">${stars}</span> (${s.score})</td>
                    <td>${rank}</td>
                </tr>
            `;
  });

  new Chart(document.getElementById("shipperChart"), {
    type: "doughnut",
    data: {
      labels: shippers.map((s) => s.name),
      datasets: [
        {
          data: shippers.map((s) => s.score),
          backgroundColor: [
            "#ff6f61", // đỏ cam pastel
            "#6ab04c", // xanh lá dịu
            "#45aaf2", // xanh dương
            "#f7b731", // vàng đậm
            "#9b59b6", // tím pastel
          ],
          borderWidth: 1,
        },
      ],
    },
    options: {
      plugins: {
        legend: {
          position: "bottom",
          labels: {
            color: "#333",
            font: { size: 14 },
          },
        },
      },
    },
  });
}

// 1. Hàm load danh sách cửa hàng khi trang vừa tải
async function loadStores() {
  try {
    const res = await fetch("http://localhost:8000/stores");
    const stores = await res.json();

    const storeSelect = document.getElementById("storeSelect");
    storeSelect.innerHTML = ""; // Xóa chữ "Đang tải..."

    // Duyệt qua danh sách và tạo thẻ <option>
    stores.forEach((store, index) => {
      const option = document.createElement("option");
      option.value = store.maCuaHang;
      option.text = store.tenCuaHang; // Hiển thị tên (VD: Shop Chủ Tech)

      // Mặc định chọn shop đầu tiên
      if (index === 0) option.selected = true;

      storeSelect.appendChild(option);
    });

    // Load xong thì vẽ biểu đồ luôn cho shop đầu tiên
    renderChart();
  } catch (error) {
    console.error("Lỗi tải danh sách cửa hàng:", error);
  }
}

// 2. Cập nhật hàm vẽ biểu đồ để lấy store_id động
async function renderChart() {
  const month = document.getElementById("monthSelect").value;
  // Lưu ý: Đã thêm id="yearInput" vào thẻ input năm ở bước HTML
  const year = document.getElementById("yearInput").value;

  // LẤY ID CỬA HÀNG TỪ DROPDOWN
  const storeId = document.getElementById("storeSelect").value;

  // Gửi store_id lên Backend
  const res = await fetch(
    `http://localhost:8000/analytics/revenue?month=${month}&year=${year}&store_id=${storeId}`
  );
  const apiData = await res.json();

  const ctx = document.getElementById("revenueChart").getContext("2d");
  if (revChartInstance) revChartInstance.destroy();

  revChartInstance = new Chart(ctx, {
    type: "bar",
    data: {
      labels: apiData.labels,
      datasets: [
        {
          label: "Doanh Thu (Triệu VNĐ)",
          data: apiData.values,
          backgroundColor: "#ee4d2d",
          barThickness: 50,
          borderRadius: 4,
        },
      ],
    },
    options: { responsive: true, maintainAspectRatio: false },
  });
}

// Gọi hàm loadStores khi trang web tải xong
window.onload = loadStores;

document.addEventListener("DOMContentLoaded", () => {
  renderChart();
  initShipper();
});
