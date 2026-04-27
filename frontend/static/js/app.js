const currencyFormatter = new Intl.NumberFormat("vi-VN", {
    style: "currency",
    currency: "VND",
    maximumFractionDigits: 0,
});

const numberFormatter = new Intl.NumberFormat("vi-VN");

function setText(id, value) {
    document.getElementById(id).textContent = value;
}

function badge(text, type = "muted") {
    return `<span class="badge badge-${type}">${text}</span>`;
}

function formatEngine(engine) {
    const labels = {
        sqlserver: "SQL Server",
        postgresql: "PostgreSQL",
        mysql: "MySQL",
    };
    return labels[engine] || engine || "Chưa rõ";
}

function renderEmpty(targetId, columnCount, message) {
    document.getElementById(targetId).innerHTML = `
        <tr><td class="empty" colspan="${columnCount}">${message}</td></tr>
    `;
}

async function fetchJson(url) {
    const response = await fetch(url);
    if (!response.ok) {
        throw new Error(`Request failed: ${response.status}`);
    }
    return response.json();
}

function renderBranches(branches) {
    setText("branchCount", numberFormatter.format(branches.length));
    setText("branchStatus", `${branches.length} chi nhánh`);

    if (!branches.length) {
        renderEmpty("branchRows", 4, "Chưa có dữ liệu chi nhánh.");
        return;
    }

    document.getElementById("branchRows").innerHTML = branches.map((branch) => {
        const configured = branch.trang_thai_ket_noi === "configured";
        return `
            <tr>
                <td>${branch.ma_chi_nhanh}</td>
                <td>${branch.ten_chi_nhanh}</td>
                <td>${badge(formatEngine(branch.he_quan_tri_csdl), "muted")}</td>
                <td>${badge(configured ? "Đã cấu hình" : "Chưa cấu hình", configured ? "ok" : "warn")}</td>
            </tr>
        `;
    }).join("");
}

function renderProducts(payload) {
    const products = payload.data || [];
    setText("productCount", numberFormatter.format(products.length));
    setText("productSource", `Nguồn: ${payload.source || "api"}`);

    if (!products.length) {
        renderEmpty("productRows", 6, "Chưa có dữ liệu sản phẩm.");
        return;
    }

    document.getElementById("productRows").innerHTML = products.map((product) => `
        <tr>
            <td>${product.ma_sp}</td>
            <td>${product.ten_sp}</td>
            <td>${product.ten_loai_sp}</td>
            <td>${product.ten_NCC}</td>
            <td class="right">${currencyFormatter.format(product.gia || 0)}</td>
            <td class="right">${product.ti_le_giam_gia || 0}%</td>
        </tr>
    `).join("");
}

function renderEmployees(employees) {
    setText("employeeCount", numberFormatter.format(employees.length));
    setText("employeeStatus", `${employees.length} nhân viên`);

    if (!employees.length) {
        renderEmpty("employeeRows", 6, "Chưa có dữ liệu nhân viên.");
        return;
    }

    document.getElementById("employeeRows").innerHTML = employees.map((employee) => {
        const active = Number(employee.trang_thai) === 1;
        return `
            <tr>
                <td>${employee.ma_nhan_vien}</td>
                <td>${employee.ho_ten}</td>
                <td>${employee.ten_pb}</td>
                <td>${employee.chuc_vu}</td>
                <td class="right">${currencyFormatter.format(employee.luong || 0)}</td>
                <td>${badge(active ? "Đang làm" : "Đã nghỉ", active ? "ok" : "muted")}</td>
            </tr>
        `;
    }).join("");
}

async function loadData() {
    setText("branchStatus", "Đang tải");
    setText("productSource", "Đang tải");
    setText("employeeStatus", "Đang tải");

    try {
        const [branches, products, employees] = await Promise.all([
            fetchJson("/api/thong-ke"),
            fetchJson("/api/san-pham"),
            fetchJson("/api/nhan-vien"),
        ]);

        renderBranches(branches);
        renderProducts(products);
        renderEmployees(employees);
    } catch (error) {
        console.error(error);
        setText("branchStatus", "Lỗi tải dữ liệu");
        setText("productSource", "Lỗi tải dữ liệu");
        setText("employeeStatus", "Lỗi tải dữ liệu");
        renderEmpty("branchRows", 4, "Không tải được dữ liệu từ API.");
        renderEmpty("productRows", 6, "Không tải được dữ liệu từ API.");
        renderEmpty("employeeRows", 6, "Không tải được dữ liệu từ API.");
    }
}

document.getElementById("refreshBtn").addEventListener("click", loadData);
loadData();
