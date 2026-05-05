const TOKEN_KEY = "techstore_token";
const USER_KEY = "techstore_user";

const pageTitles = {
    overviewView: "Tổng quan",
    branchesView: "Chi nhánh",
    productsView: "Sản phẩm",
    employeesView: "Nhân viên",
};

const currencyFormatter = new Intl.NumberFormat("vi-VN", {
    style: "currency",
    currency: "VND",
    maximumFractionDigits: 0,
});

const numberFormatter = new Intl.NumberFormat("vi-VN");

const loginView = document.getElementById("loginView");
const appView = document.getElementById("appView");
const loginForm = document.getElementById("loginForm");
const loginBtn = document.getElementById("loginBtn");
const loginError = document.getElementById("loginError");
const navItems = Array.from(document.querySelectorAll("[data-view]"));
const viewPanels = Array.from(document.querySelectorAll(".view-panel"));

function getToken() {
    return localStorage.getItem(TOKEN_KEY);
}

function getStoredUser() {
    try {
        return JSON.parse(localStorage.getItem(USER_KEY) || "null");
    } catch {
        return null;
    }
}

function setSession(token, user) {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(USER_KEY, JSON.stringify(user));
}

function clearSession() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
}

function setText(id, value) {
    document.getElementById(id).textContent = value;
}

function escapeHtml(value) {
    return String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function badge(text, type = "muted") {
    return `<span class="badge badge-${type}">${escapeHtml(text)}</span>`;
}

function formatEngine(engine) {
    const labels = {
        sqlserver: "SQL Server",
        postgresql: "PostgreSQL",
        mysql: "MySQL",
    };
    return labels[engine] || engine || "Chưa rõ";
}

function formatRole(role) {
    const labels = {
        admin: "Quản trị",
        giam_doc: "Giám đốc",
        truong_phong: "Trưởng phòng",
        pho_phong: "Phó phòng",
        nhan_vien: "Nhân viên",
    };
    return labels[role] || role || "Người dùng";
}

function renderEmpty(targetId, columnCount, message) {
    document.getElementById(targetId).innerHTML = `
        <tr><td class="empty" colspan="${columnCount}">${escapeHtml(message)}</td></tr>
    `;
}

async function fetchJson(url, options = {}) {
    const headers = new Headers(options.headers || {});
    const token = getToken();

    if (options.body && !headers.has("Content-Type")) {
        headers.set("Content-Type", "application/json");
    }
    if (token && !headers.has("Authorization")) {
        headers.set("Authorization", `Bearer ${token}`);
    }

    const response = await fetch(url, { ...options, headers });
    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
        const message = data.error || `Request failed: ${response.status}`;
        const error = new Error(message);
        error.status = response.status;
        throw error;
    }
    return data;
}

function switchView(viewId) {
    if (!pageTitles[viewId]) {
        return;
    }

    viewPanels.forEach((panel) => {
        panel.classList.toggle("active", panel.id === viewId);
    });
    navItems.forEach((item) => {
        item.classList.toggle("active", item.dataset.view === viewId);
    });
    setText("pageTitle", pageTitles[viewId]);
}

function showLogin(message = "") {
    appView.classList.add("hidden");
    loginView.classList.remove("hidden");
    loginError.textContent = message;
    loginBtn.disabled = false;
}

function showApp(user) {
    loginView.classList.add("hidden");
    appView.classList.remove("hidden");

    const role = formatRole(user.chuc_vu);
    const name = user.ho_ten || user.ma_nhan_vien || "Người dùng";
    setText("userLabel", `${name} - ${role}`);
    setText("sidebarUser", `${name}\n${role}`);
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
                <td>${escapeHtml(branch.ma_chi_nhanh)}</td>
                <td>${escapeHtml(branch.ten_chi_nhanh)}</td>
                <td>${badge(formatEngine(branch.he_quan_tri_csdl), "muted")}</td>
                <td>${badge(configured ? "Đã cấu hình" : "Chưa cấu hình", configured ? "ok" : "warn")}</td>
            </tr>
        `;
    }).join("");
}

function renderProducts(payload) {
    const products = payload.data || [];
    const source = payload.source || "api";
    setText("productCount", numberFormatter.format(products.length));
    setText("productSource", `Nguồn: ${source}`);
    setText("overviewProductSource", source);

    if (!products.length) {
        renderEmpty("productRows", 6, "Chưa có dữ liệu sản phẩm.");
        return;
    }

    document.getElementById("productRows").innerHTML = products.map((product) => `
        <tr>
            <td>${escapeHtml(product.ma_sp)}</td>
            <td>${escapeHtml(product.ten_sp)}</td>
            <td>${escapeHtml(product.ten_loai_sp)}</td>
            <td>${escapeHtml(product.ten_NCC)}</td>
            <td class="right">${currencyFormatter.format(product.gia || 0)}</td>
            <td class="right">${escapeHtml(product.ti_le_giam_gia || 0)}%</td>
        </tr>
    `).join("");
}

function renderEmployees(payload) {
    const employees = Array.isArray(payload) ? payload : (payload.data || []);
    const total = payload && payload.pagination ? payload.pagination.total : employees.length;
    setText("employeeCount", numberFormatter.format(total));
    setText("employeeStatus", `${total} nhân viên`);

    if (!employees.length) {
        renderEmpty("employeeRows", 6, "Chưa có dữ liệu nhân viên.");
        return;
    }

    document.getElementById("employeeRows").innerHTML = employees.map((employee) => {
        const active = Number(employee.trang_thai) === 1;
        return `
            <tr>
                <td>${escapeHtml(employee.ma_nhan_vien)}</td>
                <td>${escapeHtml(employee.ho_ten)}</td>
                <td>${escapeHtml(employee.ten_pb)}</td>
                <td>${escapeHtml(formatRole(employee.chuc_vu))}</td>
                <td class="right">${currencyFormatter.format(employee.luong || 0)}</td>
                <td>${badge(active ? "Đang làm" : "Đã nghỉ", active ? "ok" : "muted")}</td>
            </tr>
        `;
    }).join("");
}

async function loadData() {
    setText("overviewStatus", "Đang tải");
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
        setText("overviewStatus", "Đã đồng bộ");
    } catch (error) {
        console.error(error);
        if (error.status === 401) {
            clearSession();
            showLogin("Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.");
            return;
        }

        setText("overviewStatus", "Lỗi tải dữ liệu");
        setText("branchStatus", "Lỗi tải dữ liệu");
        setText("productSource", "Lỗi tải dữ liệu");
        setText("employeeStatus", "Lỗi tải dữ liệu");
        renderEmpty("branchRows", 4, "Không tải được dữ liệu từ API.");
        renderEmpty("productRows", 6, "Không tải được dữ liệu từ API.");
        renderEmpty("employeeRows", 6, "Không tải được dữ liệu từ API.");
    }
}

async function handleLogin(event) {
    event.preventDefault();
    loginError.textContent = "";
    loginBtn.disabled = true;

    const formData = new FormData(loginForm);
    const payload = {
        ma_nhan_vien: formData.get("ma_nhan_vien").trim(),
        mat_khau: formData.get("mat_khau"),
    };

    try {
        const result = await fetchJson("/api/auth/login", {
            method: "POST",
            body: JSON.stringify(payload),
        });
        setSession(result.token, result.user);
        showApp(result.user);
        switchView("overviewView");
        await loadData();
    } catch (error) {
        loginError.textContent = error.message || "Đăng nhập không thành công.";
    } finally {
        loginBtn.disabled = false;
    }
}

async function restoreSession() {
    const token = getToken();
    const user = getStoredUser();
    if (!token || !user) {
        showLogin();
        return;
    }

    try {
        const freshUser = await fetchJson("/api/auth/me");
        setSession(token, freshUser);
        showApp(freshUser);
        switchView("overviewView");
        await loadData();
    } catch {
        clearSession();
        showLogin();
    }
}

loginForm.addEventListener("submit", handleLogin);
document.getElementById("refreshBtn").addEventListener("click", loadData);
document.getElementById("logoutBtn").addEventListener("click", () => {
    clearSession();
    showLogin();
});
navItems.forEach((item) => {
    item.addEventListener("click", () => switchView(item.dataset.view));
});

restoreSession();
