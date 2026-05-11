const RUNTIME_CONFIG = window.__TECHSTORE_CONFIG__ || {};

const PORTALS = {
    central: {
        key: "central",
        aliases: ["/sqlserver", "/trung-tam"],
        portalLabel: "Web trung tâm SQL Server",
        portalBadge: "SQL Server trung tâm",
        loginTitle: "Đăng nhập web trung tâm",
        loginDescription: "Theo dõi dữ liệu trung tâm và xem nhanh tình trạng chi nhánh CN01 từ MySQL.",
        brandSubtitle: "Portal trung tâm",
        loginEndpoint: "/api/auth/login",
        defaultView: "overviewView",
        defaultProductSource: "main",
        mainDbLabel: "SQL Server",
        overviewScopeLabel: "Trung tâm SQL Server",
        companionLabel: "Mở web CN01",
        companionHref: "/mysql/cn01",
        secondaryTitle: "Giám sát CN01",
        secondaryLabels: ["Trạng thái MySQL", "Sản phẩm CN01", "Portal chi nhánh"],
        secondaryLinkHref: "/mysql/cn01",
        secondaryLinkText: "Mở web CN01",
        allowedViews: ["overviewView", "branchesView", "productsView", "employeesView"],
    },
    cn01: {
        key: "cn01",
        aliases: ["/mysql/cn01", "/chi-nhanh/cn01"],
        branchCode: "CN01",
        portalLabel: "Web chi nhánh CN01",
        portalBadge: "MySQL chi nhánh",
        loginTitle: "Đăng nhập web chi nhánh CN01",
        loginDescription: "Chỉ hiển thị sản phẩm, nhân viên và trạng thái dữ liệu của riêng CN01.",
        brandSubtitle: "Portal chi nhánh CN01",
        loginEndpoint: "/api/auth/branches/CN01/login",
        defaultView: "overviewView",
        defaultProductSource: "branch",
        mainDbLabel: "MySQL CN01",
        overviewScopeLabel: "Chi nhánh CN01",
        companionLabel: "Mở web SQL Server",
        companionHref: "/sqlserver",
        secondaryTitle: "Kết nối chi nhánh",
        secondaryLabels: ["Trạng thái MySQL", "Phạm vi dữ liệu", "Portal trung tâm"],
        secondaryLinkHref: "/sqlserver",
        secondaryLinkText: "Mở web SQL Server",
        allowedViews: ["overviewView", "productsView", "employeesView"],
    },
    cn02: {
        key: "cn02",
        aliases: ["/postgresql/cn02", "/chi-nhanh/cn02"],
        branchCode: "CN02",
        portalLabel: "Web chi nhánh CN02",
        portalBadge: "PostgreSQL chi nhánh",
        loginTitle: "Đăng nhập web chi nhánh CN02",
        loginDescription: "Chỉ hiển thị sản phẩm, nhân viên và trạng thái dữ liệu của riêng CN02.",
        brandSubtitle: "Portal chi nhánh CN02",
        loginEndpoint: "/api/auth/branches/CN02/login",
        defaultView: "overviewView",
        defaultProductSource: "branch",
        mainDbLabel: "PostgreSQL CN02",
        overviewScopeLabel: "Chi nhánh CN02",
        companionLabel: "Mở web SQL Server",
        companionHref: "/sqlserver",
        secondaryTitle: "Kết nối chi nhánh",
        secondaryLabels: ["Trạng thái PostgreSQL", "Phạm vi dữ liệu", "Portal trung tâm"],
        secondaryLinkHref: "/sqlserver",
        secondaryLinkText: "Mở web SQL Server",
        allowedViews: ["overviewView", "productsView", "employeesView"],
    },
};

const pageTitles = {
    overviewView: "Tổng quan",
    branchesView: "Chi nhánh",
    productsView: "Sản phẩm",
    employeesView: "Nhân viên",
};

const SUPPORTED_BRANCH_CODES = ["CN01", "CN02"];
let selectedBranchSourceCode = "CN01";
const EMPLOYEE_PAGE_LIMIT = 10;

const currencyFormatter = new Intl.NumberFormat("vi-VN", {
    style: "currency",
    currency: "VND",
    maximumFractionDigits: 0,
});

const numberFormatter = new Intl.NumberFormat("vi-VN");

const portalPickerView = document.getElementById("portalPickerView");
const loginView = document.getElementById("loginView");
const appView = document.getElementById("appView");
const loginForm = document.getElementById("loginForm");
const loginBtn = document.getElementById("loginBtn");
const loginError = document.getElementById("loginError");
const navItems = Array.from(document.querySelectorAll(".nav-item[data-view]"));
const viewPanels = Array.from(document.querySelectorAll(".view-panel"));
const metricLinks = Array.from(document.querySelectorAll("[data-shortcut-view]"));
const productSourceButtons = Array.from(
    document.querySelectorAll("[data-product-source]")
);
const employeeSourceButtons = Array.from(
    document.querySelectorAll("[data-employee-source]")
);
const employeeBranchPickerButtons = Array.from(
    document.querySelectorAll("[data-employee-branch]")
);
const employeeBranchPicker = document.getElementById("employeeBranchPicker");
const employeeBranchStatus = document.getElementById("employeeBranchStatus");

const productSourcePanel = document.getElementById("productSourcePanel");
const companionPortalLink = document.getElementById("companionPortalLink");
const sidebarPortalLink = document.getElementById("sidebarPortalLink");
const loginBackLink = document.getElementById("loginBackLink");
const secondaryLink = document.getElementById("secondaryLink");
const employeeRows = document.getElementById("employeeRows");
const employeeActionHead = document.getElementById("employeeActionHead");
const employeeManageSection = document.getElementById("employeeManageSection");
const employeeForm = document.getElementById("employeeForm");
const employeeNewBtn = document.getElementById("employeeNewBtn");
const employeeCancelBtn = document.getElementById("employeeCancelBtn");
const employeeSubmitBtn = document.getElementById("employeeSubmitBtn");
const employeeFormTitle = document.getElementById("employeeFormTitle");
const employeeFormError = document.getElementById("employeeFormError");
const employeePagination = document.getElementById("employeePagination");
const employeePageInfo = document.getElementById("employeePageInfo");
const employeePrevBtn = document.getElementById("employeePrevBtn");
const employeeNextBtn = document.getElementById("employeeNextBtn");

let activePortal = resolvePortal(window.location.pathname);
let selectedProductSource = activePortal ? activePortal.defaultProductSource : "main";
let selectedEmployeeSource =
    activePortal && activePortal.key === "central" ? "central" : "branch";
let currentUser = null;
let currentEmployees = [];
let employeeFormMode = "create";
let employeeEditingCode = null;
let employeePageState = {
    central: 1,
    branch_CN01: 1,
    branch_CN02: 1,
    cn01: 1,
    cn02: 1,
};

function normalizePath(pathname) {
    if (!pathname || pathname === "/") {
        return "/";
    }
    const normalized = pathname.replace(/\/+$/, "");
    return normalized || "/";
}

function getRuntimePortal() {
    const portalKey = String(RUNTIME_CONFIG.portalKey || "")
        .trim()
        .toLowerCase();

    if (!portalKey || portalKey === "picker") {
        return null;
    }

    const portal = PORTALS[portalKey];
    if (!portal) {
        return null;
    }

    return {
        ...portal,
        aliases: Array.from(new Set(["/", ...(portal.aliases || [])])),
        loginEndpoint: RUNTIME_CONFIG.loginEndpoint || portal.loginEndpoint,
        companionHref: RUNTIME_CONFIG.companionHref || portal.companionHref,
        secondaryLinkHref: RUNTIME_CONFIG.secondaryLinkHref ||
            RUNTIME_CONFIG.companionHref ||
            portal.secondaryLinkHref,
        portalPickerHref: RUNTIME_CONFIG.portalPickerHref || "/",
    };
}

function resolvePortal(pathname) {
    const runtimePortal = getRuntimePortal();
    if (runtimePortal) {
        return runtimePortal;
    }

    const normalized = normalizePath(pathname);
    return (
        Object.values(PORTALS).find((portal) =>
            portal.aliases.some(
                (alias) =>
                normalized === alias || normalized.startsWith(`${alias}/`)
            )
        ) || null
    );
}

function getTokenKey() {
    return `techstore_token_${activePortal.key}`;
}

function getUserKey() {
    return `techstore_user_${activePortal.key}`;
}

function getToken() {
    return activePortal ? localStorage.getItem(getTokenKey()) : null;
}

function getStoredUser() {
    if (!activePortal) {
        return null;
    }

    try {
        return JSON.parse(localStorage.getItem(getUserKey()) || "null");
    } catch {
        return null;
    }
}

function setSession(token, user) {
    localStorage.setItem(getTokenKey(), token);
    localStorage.setItem(getUserKey(), JSON.stringify(user));
}

function clearSession() {
    if (!activePortal) {
        return;
    }
    currentUser = null;
    localStorage.removeItem(getTokenKey());
    localStorage.removeItem(getUserKey());
}

function setText(id, value) {
    const element = document.getElementById(id);
    if (element) {
        element.textContent = value;
    }
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

function formatHealthStatus(status) {
    const labels = {
        ok: "Kết nối ổn định",
        configured: "Đã cấu hình",
        not_configured: "Chưa cấu hình",
        unreachable: "Không kết nối được",
        unsupported_engine: "Engine chưa hỗ trợ",
    };
    return labels[status] || "Chưa rõ";
}

function renderEmpty(targetId, columnCount, message) {
    const target = document.getElementById(targetId);
    if (!target) {
        return;
    }
    target.innerHTML = `
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

    const response = await fetch(url, {...options, headers });
    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
        const message = data.error || `Request failed: ${response.status}`;
        const error = new Error(message);
        error.status = response.status;
        throw error;
    }

    return data;
}

function isUserAllowedForPortal(user) {
    if (!activePortal || !user) {
        return false;
    }

    if (activePortal.key === "central") {
        return user.scope === "central";
    }

    return (
        user.scope === "branch" &&
        (user.branch_code || "").toUpperCase() === activePortal.branchCode
    );
}

function canManageEmployees() {
    if (!currentUser || !activePortal) {
        return false;
    }

    if (activePortal.key === "central") {
        return (
            selectedEmployeeSource === "central" &&
            currentUser.scope === "central" && ["admin", "giam_doc"].includes(currentUser.chuc_vu)
        );
    }

    return (
        currentUser.scope === "branch" && ["admin", "giam_doc", "truong_phong"].includes(currentUser.chuc_vu)
    );
}

function isViewingCentralEmployees() {
    return activePortal && activePortal.key === "central" && selectedEmployeeSource === "central";
}

function isViewingBranchEmployeesFromHeadquarter() {
    return activePortal && activePortal.key === "central" && selectedEmployeeSource === "branch";
}

function getEmployeePageTitle() {
    if (isViewingCentralEmployees()) {
        return "Nhân viên trụ sở";
    }

    if (isViewingBranchEmployeesFromHeadquarter()) {
        return "Nhân viên chi nhánh";
    }

    return pageTitles.employeesView;
}

function getEmployeeManagementTitle() {
    if (isViewingCentralEmployees()) {
        return "Quản lý nhân viên trụ sở";
    }

    if (!activePortal || activePortal.key === "central") {
        return "Quản lý nhân viên";
    }

    return `Quản lý nhân viên ${activePortal.branchCode}`;
}

function getEmployeeStatusLabel(total) {
    if (isViewingCentralEmployees()) {
        return `Trụ sở - ${total} nhân viên`;
    }

    if (isViewingBranchEmployeesFromHeadquarter()) {
        return `${selectedBranchSourceCode} - ${total} nhân viên`;
    }

    return `${total} nhân viên`;
}

function syncEmployeeSourceButtons() {
    employeeSourceButtons.forEach((button) => {
        button.classList.toggle(
            "active",
            button.dataset.employeeSource === selectedEmployeeSource
        );
    });
}

function syncEmployeeBranchPicker() {
    if (!employeeBranchPicker) {
        return;
    }
    const visible = isViewingBranchEmployeesFromHeadquarter();
    employeeBranchPicker.classList.toggle("hidden", !visible);
    employeeBranchPickerButtons.forEach((button) => {
        button.classList.toggle(
            "active",
            button.dataset.employeeBranch === selectedBranchSourceCode
        );
    });
    if (employeeBranchStatus) {
        employeeBranchStatus.textContent = selectedBranchSourceCode;
    }
}

function getEmployeePaginationKey() {
    if (!activePortal) {
        return "central";
    }

    if (activePortal.key === "central") {
        return selectedEmployeeSource === "central" ?
            "central" :
            `branch_${selectedBranchSourceCode}`;
    }

    return activePortal.key;
}

function getEmployeeCurrentPage() {
    const key = getEmployeePaginationKey();
    return employeePageState[key] || 1;
}

function setEmployeeCurrentPage(page) {
    const key = getEmployeePaginationKey();
    employeePageState[key] = Math.max(1, Number(page) || 1);
}

function resetEmployeePagination() {
    employeePageState = {
        central: 1,
        cn01: 1,
        cn02: 1,
    };
    SUPPORTED_BRANCH_CODES.forEach((code) => {
        employeePageState[`branch_${code}`] = 1;
    });
}

function canDisableEmployees() {
    return (
        activePortal &&
        currentUser &&
        currentUser.scope === "branch" &&
        canManageEmployees()
    );
}

function getEmployeeColumnCount() {
    return canManageEmployees() ? 7 : 6;
}

function switchView(viewId) {
    if (!pageTitles[viewId] || !activePortal.allowedViews.includes(viewId)) {
        return;
    }

    viewPanels.forEach((panel) => {
        panel.classList.toggle("active", panel.id === viewId);
    });
    navItems.forEach((item) => {
        item.classList.toggle("active", item.dataset.view === viewId);
    });
    setText(
        "pageTitle",
        viewId === "employeesView" ? getEmployeePageTitle() : pageTitles[viewId]
    );
    syncEmployeeBranchPicker();
}

function showPortalPicker() {
    portalPickerView.classList.remove("hidden");
    loginView.classList.add("hidden");
    appView.classList.add("hidden");
}

function showLogin(message = "") {
    currentUser = null;
    portalPickerView.classList.add("hidden");
    appView.classList.add("hidden");
    loginView.classList.remove("hidden");
    loginError.textContent = message;
    loginBtn.disabled = false;
    toggleEmployeeManagementVisibility();
}

function showApp(user) {
    currentUser = user;
    portalPickerView.classList.add("hidden");
    loginView.classList.add("hidden");
    appView.classList.remove("hidden");

    const role = formatRole(user.chuc_vu);
    const name = user.ho_ten || user.ma_nhan_vien || "Người dùng";
    const scopeLabel = activePortal.key === "central" ? "Trung tâm" : activePortal.branchCode;

    setText("userLabel", `${name} - ${role} - ${scopeLabel}`);
    setText("sidebarUser", `${name}\n${role}\n${activePortal.portalLabel}`);
    toggleEmployeeManagementVisibility();
}

function configurePortalUI() {
    if (!activePortal) {
        document.title = "Tech Store Portal";
        return;
    }

    document.title = `${activePortal.portalLabel} | Tech Store`;
    setText("loginEyebrow", "Tech Store");
    setText("loginTitle", activePortal.loginTitle);
    setText("loginDescription", activePortal.loginDescription);
    setText("loginScopeTag", activePortal.portalBadge);
    setText("brandSubtitle", activePortal.brandSubtitle);
    setText("overviewDbEngine", activePortal.mainDbLabel);
    setText("overviewScope", activePortal.overviewScopeLabel);
    setText("secondaryInsightTitle", activePortal.secondaryTitle);
    setText("secondaryLabel1", activePortal.secondaryLabels[0]);
    setText("secondaryLabel2", activePortal.secondaryLabels[1]);
    setText("secondaryLabel3", activePortal.secondaryLabels[2]);

    companionPortalLink.href = activePortal.companionHref;
    companionPortalLink.textContent = activePortal.companionLabel;
    sidebarPortalLink.href = activePortal.portalPickerHref || "/";
    loginBackLink.href = activePortal.portalPickerHref || "/";
    secondaryLink.href = activePortal.secondaryLinkHref;
    secondaryLink.textContent = activePortal.secondaryLinkText;

    document.querySelectorAll("[data-central-only]").forEach((element) => {
        element.hidden = activePortal.key !== "central";
    });

    productSourcePanel.hidden = activePortal.key !== "central";
    selectedProductSource = activePortal.defaultProductSource;
    selectedEmployeeSource = activePortal.key === "central" ? "central" : "branch";
    selectedBranchSourceCode = activePortal.branchCode || "CN01";
    resetEmployeePagination();
    syncProductSourceButtons();
    syncEmployeeSourceButtons();
    syncEmployeeBranchPicker();
    resetEmployeeForm();
    toggleEmployeeManagementVisibility();
    switchView(activePortal.defaultView);
}

function syncProductSourceButtons() {
    productSourceButtons.forEach((button) => {
        button.classList.toggle(
            "active",
            button.dataset.productSource === selectedProductSource
        );
    });
}

function toggleEmployeeManagementVisibility() {
    const visible = canManageEmployees();
    employeeManageSection.classList.toggle("hidden", !visible);
    employeeActionHead.classList.toggle("hidden", !visible);
    if (!visible) {
        employeeCancelBtn.classList.add("hidden");
    }
}

function resetEmployeeForm() {
    employeeForm.reset();
    employeeFormMode = "create";
    employeeEditingCode = null;
    employeeFormTitle.textContent = getEmployeeManagementTitle();
    employeeSubmitBtn.textContent = "Lưu nhân viên";
    employeeFormError.textContent = "";
    document.getElementById("employeeFormStatus").value = "1";
    document.getElementById("employeeFormRole").value = "nhan_vien";
    document.getElementById("employeeFormCode").disabled = false;
    employeeCancelBtn.classList.add("hidden");
}

function fillEmployeeForm(employee) {
    employeeFormMode = "edit";
    employeeEditingCode = employee.ma_nhan_vien;
    employeeFormTitle.textContent = `Cập nhật ${employee.ma_nhan_vien}`;
    employeeSubmitBtn.textContent = "Cập nhật nhân viên";
    employeeFormError.textContent = "";
    employeeCancelBtn.classList.remove("hidden");

    document.getElementById("employeeFormCode").value = employee.ma_nhan_vien || "";
    document.getElementById("employeeFormCode").disabled = true;
    document.getElementById("employeeFormName").value = employee.ho_ten || "";
    document.getElementById("employeeFormPassword").value = "";
    document.getElementById("employeeFormDepartment").value =
        employee.ma_phong_ban ?? "";
    document.getElementById("employeeFormRole").value = employee.chuc_vu || "nhan_vien";
    document.getElementById("employeeFormSalary").value = employee.luong ?? "";
    document.getElementById("employeeFormPhone").value = employee.sdt || "";
    document.getElementById("employeeFormCccd").value = employee.cccd || "";
    document.getElementById("employeeFormDays").value = employee.ma_ngay_lam ?? "";
    document.getElementById("employeeFormStatus").value =
        String(employee.trang_thai ?? 1);
    document.getElementById("employeeFormStartDate").value =
        employee.ngay_bat_dau ? employee.ngay_bat_dau.slice(0, 10) : "";
    document.getElementById("employeeFormEndDate").value =
        employee.ngay_ket_thuc ? employee.ngay_ket_thuc.slice(0, 10) : "";
}

function collectEmployeePayload() {
    const getValue = (id) => document.getElementById(id).value.trim();
    const payload = {
        ho_ten: getValue("employeeFormName"),
        ma_phong_ban: Number(getValue("employeeFormDepartment")),
        chuc_vu: getValue("employeeFormRole") || "nhan_vien",
        trang_thai: Number(getValue("employeeFormStatus") || "1"),
    };

    if (employeeFormMode === "create") {
        payload.ma_nhan_vien = getValue("employeeFormCode");
    }

    const password = getValue("employeeFormPassword");
    if (employeeFormMode === "create") {
        if (!password) {
            throw new Error("Mật khẩu là bắt buộc khi thêm mới.");
        }
        payload.mat_khau = password;
    } else if (password) {
        payload.mat_khau = password;
    }

    const optionalTextFields = [
        ["cccd", "employeeFormCccd"],
        ["sdt", "employeeFormPhone"],
        ["ngay_bat_dau", "employeeFormStartDate"],
        ["ngay_ket_thuc", "employeeFormEndDate"],
    ];
    optionalTextFields.forEach(([field, id]) => {
        const value = getValue(id);
        if (employeeFormMode === "create" || value !== "") {
            payload[field] = value || null;
        }
    });

    const optionalNumberFields = [
        ["luong", "employeeFormSalary"],
        ["ma_ngay_lam", "employeeFormDays"],
    ];
    optionalNumberFields.forEach(([field, id]) => {
        const value = getValue(id);
        if (employeeFormMode === "create" || value !== "") {
            payload[field] = value === "" ? null : Number(value);
        }
    });

    return payload;
}

function renderBranches(branches) {
    if (activePortal.key !== "central") {
        return;
    }

    setText("branchStatus", `${branches.length} chi nhánh`);
    setText("contextMetricLabel", "Chi nhánh hoạt động");
    setText("contextMetricValue", numberFormatter.format(branches.length));

    if (!branches.length) {
        renderEmpty("branchRows", 4, "Chưa có dữ liệu chi nhánh.");
        return;
    }

    document.getElementById("branchRows").innerHTML = branches
        .map((branch) => {
            const configured = branch.trang_thai_ket_noi === "configured";
            return `
                <tr>
                    <td>${escapeHtml(branch.ma_chi_nhanh)}</td>
                    <td>${escapeHtml(branch.ten_chi_nhanh)}</td>
                    <td>${badge(formatEngine(branch.he_quan_tri_csdl), "muted")}</td>
                    <td>${badge(
                        configured ? "Đã cấu hình" : "Chưa cấu hình",
                        configured ? "ok" : "warn"
                    )}</td>
                </tr>
            `;
        })
        .join("");
}

function getProductSourceLabel(payload) {
    if (payload.branch && payload.engine) {
        return `${payload.branch.ten_chi_nhanh} - ${formatEngine(payload.engine)}`;
    }

    if (activePortal.key === "central") {
        return selectedProductSource === "main" ?
            "SQL Server trung tâm" :
            "CN01 - MySQL";
    }

    return activePortal.mainDbLabel;
}

function renderProducts(payload) {
    const products = payload.data || [];
    const sourceLabel = getProductSourceLabel(payload);
    const total = payload.pagination ? payload.pagination.total : products.length;

    setText("productCount", numberFormatter.format(total));
    setText("productSource", `Nguồn: ${sourceLabel}`);
    setText("overviewProductSource", sourceLabel);

    if (activePortal.key === "central") {
        setText(
            "branchDbStatus",
            selectedProductSource === "main" ? "DB chính - SQL Server" : sourceLabel
        );
    }

    if (!products.length) {
        renderEmpty("productRows", 6, "Chưa có dữ liệu sản phẩm.");
        return;
    }

    document.getElementById("productRows").innerHTML = products
        .map(
            (product) => `
                <tr>
                    <td>${escapeHtml(product.ma_sp)}</td>
                    <td>${escapeHtml(product.ten_sp)}</td>
                    <td>${escapeHtml(product.ten_loai_sp)}</td>
                    <td>${escapeHtml(product.ten_NCC)}</td>
                    <td class="right">${currencyFormatter.format(product.gia || 0)}</td>
                    <td class="right">${escapeHtml(product.ti_le_giam_gia || 0)}%</td>
                </tr>
            `
        )
        .join("");
}

async function fetchProductsForActivePortal() {
    if (activePortal.key === "central") {
        if (selectedProductSource === "main") {
            setText("branchDbStatus", "DB chính - SQL Server");
            return fetchJson("/api/san-pham");
        }

        setText("branchDbStatus", `Đang đọc ${selectedProductSource}`);
        return fetchJson(`/api/chi-nhanh/${selectedProductSource}/san-pham`);
    }

    return fetchJson("/api/san-pham");
}

function getEmployeePaginationParams() {
    const params = new URLSearchParams();
    params.set("page", String(getEmployeeCurrentPage()));
    params.set("limit", String(EMPLOYEE_PAGE_LIMIT));
    return params.toString();
}

async function fetchEmployeesForActivePortal() {
    const query = getEmployeePaginationParams();
    if (isViewingBranchEmployeesFromHeadquarter()) {
        return fetchJson(
            `/api/chi-nhanh/${selectedBranchSourceCode}/nhan-vien?${query}`
        );
    }

    return fetchJson(`/api/nhan-vien?${query}`);
}

function getEmployeeTotal(payload) {
    if (Array.isArray(payload)) {
        return payload.length;
    }
    if (payload && payload.pagination) {
        return payload.pagination.total;
    }
    return payload && payload.data ? payload.data.length : 0;
}

function getEmployeePaginationMeta(payload, employees) {
    if (payload && payload.pagination) {
        return payload.pagination;
    }

    const total = Array.isArray(payload) ?
        payload.length :
        payload && payload.data ?
        payload.data.length :
        employees.length;

    return {
        page: 1,
        limit: EMPLOYEE_PAGE_LIMIT,
        total,
        total_pages: total > 0 ? 1 : 0,
    };
}

function renderEmployeePagination(payload, employees) {
    const pagination = getEmployeePaginationMeta(payload, employees);
    const total = Number(pagination.total) || 0;
    const totalPages = Number(pagination.total_pages) || 0;
    const safePage = totalPages > 0 ?
        Math.min(Math.max(Number(pagination.page) || 1, 1), totalPages) :
        1;

    setEmployeeCurrentPage(safePage);
    employeePageInfo.textContent = total ?
        `Trang ${safePage} / ${totalPages} - ${numberFormatter.format(total)} nhân viên` :
        "Chưa có dữ liệu nhân viên";
    employeePrevBtn.disabled = safePage <= 1;
    employeeNextBtn.disabled = totalPages === 0 || safePage >= totalPages;
}

function renderEmployees(payload) {
    const employees = Array.isArray(payload) ? payload : payload.data || [];
    const total = getEmployeeTotal(payload);
    const canManage = canManageEmployees();
    const canDisable = canDisableEmployees();

    currentEmployees = employees;
    setText("employeeCount", numberFormatter.format(total));
    setText("employeeStatus", getEmployeeStatusLabel(total));
    employeeActionHead.classList.toggle("hidden", !canManage);
    renderEmployeePagination(payload, employees);

    if (!employees.length) {
        renderEmpty(
            "employeeRows",
            getEmployeeColumnCount(),
            "Chưa có dữ liệu nhân viên."
        );
        return;
    }

    employeeRows.innerHTML = employees
        .map((employee) => {
                const active = Number(employee.trang_thai) === 1;
                const actionCell = canManage ?
                    `
                    <td class="right">
                        <div class="row-actions">
                            <button class="table-btn" type="button" data-employee-action="edit" data-employee-id="${escapeHtml(
                                employee.ma_nhan_vien
                            )}">
                                Sửa
                            </button>
                            ${
                                canDisable
                                    ? `
                                        <button
                                            class="table-btn table-btn-danger"
                                            type="button"
                                            data-employee-action="disable"
                                            data-employee-id="${escapeHtml(employee.ma_nhan_vien)}"
                                            ${active ? "" : "disabled"}
                                        >
                                            Ngưng
                                        </button>
                                    `
                                    : ""
                            }
                        </div>
                    </td>
                `
                : "";

            return `
                <tr>
                    <td>${escapeHtml(employee.ma_nhan_vien)}</td>
                    <td>${escapeHtml(employee.ho_ten)}</td>
                    <td>${escapeHtml(employee.ten_pb)}</td>
                    <td>${escapeHtml(formatRole(employee.chuc_vu))}</td>
                    <td class="right">${currencyFormatter.format(employee.luong || 0)}</td>
                    <td>${badge(active ? "Đang làm" : "Đã nghỉ", active ? "ok" : "muted")}</td>
                    ${actionCell}
                </tr>
            `;
        })
        .join("");
}
// tets

function renderCentralInsight(health, branchProducts) {
    const productCount =
        branchProducts?.pagination?.total ?? branchProducts?.data?.length ?? 0;
    setText("secondaryInsightStatus", formatHealthStatus(health.status));
    setText("secondaryValue1", formatHealthStatus(health.status));
    setText("secondaryValue2", numberFormatter.format(productCount));
    secondaryLink.href = activePortal.secondaryLinkHref;
    secondaryLink.textContent = activePortal.secondaryLinkText;
}

function renderBranchInsight(health, employeesPayload) {
    setText("contextMetricLabel", "Phạm vi dữ liệu");
    setText("contextMetricValue", activePortal.branchCode);
    setText("secondaryInsightStatus", formatHealthStatus(health.status));
    setText("secondaryValue1", formatHealthStatus(health.status));
    setText(
        "secondaryValue2",
        `${activePortal.branchCode} - ${numberFormatter.format(
            getEmployeeTotal(employeesPayload)
        )} nhân viên`
    );
    secondaryLink.href = activePortal.secondaryLinkHref;
    secondaryLink.textContent = activePortal.secondaryLinkText;
}

function setLoadingState() {
    setText("overviewStatus", "Đang tải");
    setText("productSource", "Đang tải");
    setText("employeeStatus", "Đang tải");
    setText("secondaryInsightStatus", "Đang tải");
    employeePageInfo.textContent = "Đang tải phân trang";
    employeePrevBtn.disabled = true;
    employeeNextBtn.disabled = true;

    if (activePortal.key === "central") {
        setText("branchStatus", "Đang tải");
    }
}

function renderApiError(message) {
    setText("overviewStatus", "Lỗi tải dữ liệu");
    setText("productSource", "Lỗi tải dữ liệu");
    setText("employeeStatus", "Lỗi tải dữ liệu");
    setText("secondaryInsightStatus", "Lỗi tải dữ liệu");
    employeePageInfo.textContent = "Không tải được phân trang";
    employeePrevBtn.disabled = true;
    employeeNextBtn.disabled = true;

    if (activePortal.key === "central") {
        setText("branchStatus", "Lỗi tải dữ liệu");
        renderEmpty("branchRows", 4, message);
    }

    renderEmpty("productRows", 6, message);
    renderEmpty("employeeRows", getEmployeeColumnCount(), message);
}

async function loadCentralData() {
    const insightBranch = selectedBranchSourceCode || "CN01";
    const [branches, products, employees, branchHealth, branchProducts] =
        await Promise.all([
            fetchJson("/api/thong-ke"),
            fetchProductsForActivePortal(),
            fetchEmployeesForActivePortal(),
            fetchJson(`/api/chi-nhanh/${insightBranch}/health`),
            fetchJson(`/api/chi-nhanh/${insightBranch}/san-pham`),
        ]);

    renderBranches(branches);
    renderProducts(products);
    renderEmployees(employees);
    renderCentralInsight(branchHealth, branchProducts);
    setText("overviewStatus", "Đã đồng bộ");
}

async function loadBranchData() {
    const [products, employees, branchHealth] = await Promise.all([
        fetchProductsForActivePortal(),
        fetchEmployeesForActivePortal(),
        fetchJson(`/api/chi-nhanh/${activePortal.branchCode}/health`),
    ]);

    renderProducts(products);
    renderEmployees(employees);
    renderBranchInsight(branchHealth, employees);
    setText("overviewStatus", "Đã đồng bộ");
}

async function loadData() {
    if (!activePortal) {
        return;
    }

    setLoadingState();

    try {
        if (activePortal.key === "central") {
            await loadCentralData();
        } else {
            await loadBranchData();
        }
    } catch (error) {
        console.error(error);

        if (error.status === 401) {
            clearSession();
            showLogin("Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.");
            return;
        }

        renderApiError("Không tải được dữ liệu từ API.");
    }
}

async function submitEmployeeForm(event) {
    event.preventDefault();
    if (!canManageEmployees()) {
        return;
    }

    employeeFormError.textContent = "";
    employeeSubmitBtn.disabled = true;

    try {
        const payload = collectEmployeePayload();
        const isCreate = employeeFormMode === "create";
        const url = isCreate
            ? "/api/nhan-vien"
            : `/api/nhan-vien/${employeeEditingCode}`;
        const method = isCreate ? "POST" : "PUT";

        await fetchJson(url, {
            method,
            body: JSON.stringify(payload),
        });

        resetEmployeeForm();
        await loadData();
        switchView("employeesView");
        setText(
            "employeeStatus",
            isCreate ? "Đã thêm nhân viên mới" : "Đã cập nhật nhân viên"
        );
    } catch (error) {
        employeeFormError.textContent =
            error.message || "Không lưu được thông tin nhân viên.";
    } finally {
        employeeSubmitBtn.disabled = false;
    }
}

async function handleEmployeeRowClick(event) {
    const actionButton = event.target.closest("[data-employee-action]");
    if (!actionButton || !canManageEmployees()) {
        return;
    }

    const employeeId = actionButton.dataset.employeeId;
    const action = actionButton.dataset.employeeAction;

    if (!employeeId) {
        return;
    }

    if (action === "edit") {
        try {
            const employee = await fetchJson(`/api/nhan-vien/${employeeId}`);
            fillEmployeeForm(employee);
            switchView("employeesView");
        } catch (error) {
            employeeFormError.textContent =
                error.message || "Không tải được thông tin nhân viên.";
        }
        return;
    }

    if (action === "disable") {
        if (!canDisableEmployees()) {
            return;
        }
        const confirmed = window.confirm(
            `Ngưng nhân viên ${employeeId} trong chi nhánh ${activePortal.branchCode}?`
        );
        if (!confirmed) {
            return;
        }

        try {
            await fetchJson(`/api/nhan-vien/${employeeId}`, {
                method: "DELETE",
            });
            if (employeeEditingCode === employeeId) {
                resetEmployeeForm();
            }
            await loadData();
            setText("employeeStatus", `Đã ngưng nhân viên ${employeeId}`);
        } catch (error) {
            employeeFormError.textContent =
                error.message || "Không ngưng được nhân viên.";
        }
    }
}

async function changeEmployeePage(step) {
    const nextPage = getEmployeeCurrentPage() + step;
    if (nextPage < 1) {
        return;
    }

    setEmployeeCurrentPage(nextPage);
    switchView("employeesView");
    await loadData();
}

async function handleLogin(event) {
    event.preventDefault();
    loginError.textContent = "";
    loginBtn.disabled = true;

    const formData = new FormData(loginForm);
    const payload = {
        ma_nhan_vien: String(formData.get("ma_nhan_vien") || "").trim(),
        mat_khau: formData.get("mat_khau"),
    };

    try {
        const result = await fetchJson(activePortal.loginEndpoint, {
            method: "POST",
            body: JSON.stringify(payload),
        });

        if (!isUserAllowedForPortal(result.user)) {
            throw new Error("Tài khoản này không thuộc portal đang mở.");
        }

        setSession(result.token, result.user);
        showApp(result.user);
        switchView(activePortal.defaultView);
        await loadData();
    } catch (error) {
        loginError.textContent = error.message || "Đăng nhập không thành công.";
    } finally {
        loginBtn.disabled = false;
    }
}

async function restoreSession() {
    if (!activePortal) {
        showPortalPicker();
        return;
    }

    configurePortalUI();

    const token = getToken();
    const user = getStoredUser();
    if (!token || !user) {
        showLogin();
        return;
    }

    try {
        const freshUser = await fetchJson("/api/auth/me");
        if (!isUserAllowedForPortal(freshUser)) {
            throw new Error("Portal mismatch");
        }

        setSession(token, freshUser);
        showApp(freshUser);
        switchView(activePortal.defaultView);
        await loadData();
    } catch (error) {
        clearSession();
        const message =
            error.message === "Portal mismatch"
                ? "Phiên đăng nhập này thuộc portal khác. Vui lòng đăng nhập lại."
                : "";
        showLogin(message);
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

metricLinks.forEach((item) => {
    item.addEventListener("click", () => switchView(item.dataset.shortcutView));
});

productSourceButtons.forEach((button) => {
    button.addEventListener("click", async () => {
        if (activePortal.key !== "central") {
            return;
        }

        selectedProductSource = button.dataset.productSource;
        syncProductSourceButtons();
        switchView("productsView");
        await loadData();
    });
});

employeeSourceButtons.forEach((button) => {
    button.addEventListener("click", async () => {
        if (activePortal.key !== "central") {
            return;
        }

        selectedEmployeeSource = button.dataset.employeeSource || "central";
        syncEmployeeSourceButtons();
        syncEmployeeBranchPicker();
        resetEmployeeForm();
        toggleEmployeeManagementVisibility();
        switchView("employeesView");
        await loadData();
    });
});

employeeBranchPickerButtons.forEach((button) => {
    button.addEventListener("click", async () => {
        if (activePortal.key !== "central") {
            return;
        }
        const code = button.dataset.employeeBranch;
        if (!code || code === selectedBranchSourceCode) {
            return;
        }
        selectedBranchSourceCode = code;
        syncEmployeeBranchPicker();
        switchView("employeesView");
        await loadData();
    });
});

employeeNewBtn.addEventListener("click", () => {
    resetEmployeeForm();
    switchView("employeesView");
});

employeeCancelBtn.addEventListener("click", () => {
    resetEmployeeForm();
});

employeeForm.addEventListener("submit", submitEmployeeForm);
employeeRows.addEventListener("click", handleEmployeeRowClick);
employeePrevBtn.addEventListener("click", async () => {
    if (employeePrevBtn.disabled) {
        return;
    }
    await changeEmployeePage(-1);
});
employeeNextBtn.addEventListener("click", async () => {
    if (employeeNextBtn.disabled) {
        return;
    }
    await changeEmployeePage(1);
});

restoreSession();