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
        allowedViews: ["overviewView", "branchesView", "productsView", "invoicesView", "employeesView"],
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
        allowedViews: ["overviewView", "productsView", "invoicesView", "employeesView"],
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
        allowedViews: ["overviewView", "productsView", "invoicesView", "employeesView"],
    },
};

const pageTitles = {
    overviewView: "Tổng quan",
    branchesView: "Chi nhánh",
    productsView: "Sản phẩm",
    invoicesView: "Hóa đơn",
    employeesView: "Nhân viên",
};

const SUPPORTED_BRANCH_CODES = ["CN01", "CN02"];
let selectedBranchSourceCode = "CN01";
const EMPLOYEE_PAGE_LIMIT = 10;
const PRODUCT_PAGE_SIZE = 10;
let productCurrentPage = 1;
let productListCache = [];
let productPayloadCache = null;

const currencyFormatter = new Intl.NumberFormat("vi-VN", {
    style: "currency",
    currency: "VND",
    maximumFractionDigits: 0,
});

const numberFormatter = new Intl.NumberFormat("vi-VN");

const overviewChartState = {
    products: 0,
    employees: 0,
    invoices: 0,
    revenueStats: null,
};

const overviewColors = {
    product: "#1f6f62",
    employee: "#3867a8",
    invoice: "#b06b26",
    revenue: "#2b7a6b",
    accent: "#6b7280",
};

function formatCompactCurrency(value) {
    const amount = Number(value) || 0;
    if (amount >= 1000000000) return `${(amount / 1000000000).toFixed(1)} tỷ`;
    if (amount >= 1000000) return `${(amount / 1000000).toFixed(1)} tr`;
    return currencyFormatter.format(amount);
}

function prepareChart(canvasId) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return null;
    const rect = canvas.getBoundingClientRect();
    const width = Math.max(280, Math.floor(rect.width || canvas.clientWidth || 320));
    const height = Math.max(220, Math.floor(rect.height || canvas.clientHeight || 240));
    const ratio = window.devicePixelRatio || 1;
    canvas.width = Math.floor(width * ratio);
    canvas.height = Math.floor(height * ratio);
    const ctx = canvas.getContext("2d");
    ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
    ctx.clearRect(0, 0, width, height);
    return { ctx, width, height };
}

function drawChartEmpty(canvasId, message) {
    const chart = prepareChart(canvasId);
    if (!chart) return;
    const { ctx, width, height } = chart;
    ctx.fillStyle = "#f8fafc";
    ctx.fillRect(0, 0, width, height);
    ctx.fillStyle = "#64717f";
    ctx.font = "700 13px Segoe UI, Arial";
    ctx.textAlign = "center";
    ctx.fillText(message, width / 2, height / 2);
}

function setChartLegend(id, items) {
    const el = document.getElementById(id);
    if (!el) return;
    el.innerHTML = items
        .map(
            (item) => `
                <span class="legend-item">
                    <span class="legend-dot" style="--legend-color: ${item.color}"></span>
                    ${escapeHtml(item.label)}
                </span>
            `
        )
        .join("");
}

function drawBarChart(canvasId, items, options = {}) {
    const visibleItems = items.filter((item) => Number(item.value) > 0);
    if (!visibleItems.length) {
        drawChartEmpty(canvasId, options.emptyText || "Chưa có dữ liệu để vẽ biểu đồ");
        return;
    }

    const chart = prepareChart(canvasId);
    if (!chart) return;
    const { ctx, width, height } = chart;
    const margin = { top: 18, right: 18, bottom: 46, left: 46 };
    const chartWidth = width - margin.left - margin.right;
    const chartHeight = height - margin.top - margin.bottom;
    const maxValue = Math.max(...visibleItems.map((item) => Number(item.value)), 1);
    const valueFormatter = options.valueFormatter || ((value) => numberFormatter.format(value));

    ctx.fillStyle = "#ffffff";
    ctx.fillRect(0, 0, width, height);
    ctx.strokeStyle = "#edf1f5";
    ctx.lineWidth = 1;
    ctx.fillStyle = "#64717f";
    ctx.font = "12px Segoe UI, Arial";
    ctx.textAlign = "right";

    for (let i = 0; i <= 4; i += 1) {
        const y = margin.top + chartHeight - (chartHeight * i) / 4;
        const value = (maxValue * i) / 4;
        ctx.beginPath();
        ctx.moveTo(margin.left, y);
        ctx.lineTo(width - margin.right, y);
        ctx.stroke();
        ctx.fillText(valueFormatter(value), margin.left - 8, y + 4);
    }

    const gap = Math.min(28, chartWidth / visibleItems.length * 0.22);
    const barWidth = Math.max(24, (chartWidth - gap * (visibleItems.length - 1)) / visibleItems.length);

    visibleItems.forEach((item, index) => {
        const x = margin.left + index * (barWidth + gap);
        const barHeight = Math.max(4, (Number(item.value) / maxValue) * chartHeight);
        const y = margin.top + chartHeight - barHeight;
        ctx.fillStyle = item.color;
        ctx.fillRect(x, y, barWidth, barHeight);
        ctx.fillStyle = "#20242a";
        ctx.font = "700 12px Segoe UI, Arial";
        ctx.textAlign = "center";
        ctx.fillText(valueFormatter(Number(item.value)), x + barWidth / 2, y - 7);
        ctx.fillStyle = "#4a5663";
        ctx.font = "12px Segoe UI, Arial";
        ctx.fillText(item.shortLabel || item.label, x + barWidth / 2, height - 18);
    });
}

function drawLineChart(canvasId, points, options = {}) {
    const visiblePoints = points.filter((point) => Number(point.value) > 0);
    if (!visiblePoints.length) {
        drawChartEmpty(canvasId, options.emptyText || "Chưa có dữ liệu để vẽ biểu đồ");
        return;
    }

    const chart = prepareChart(canvasId);
    if (!chart) return;
    const { ctx, width, height } = chart;
    const margin = { top: 18, right: 18, bottom: 46, left: 56 };
    const chartWidth = width - margin.left - margin.right;
    const chartHeight = height - margin.top - margin.bottom;
    const maxValue = Math.max(...visiblePoints.map((point) => Number(point.value)), 1);

    ctx.fillStyle = "#ffffff";
    ctx.fillRect(0, 0, width, height);
    ctx.strokeStyle = "#edf1f5";
    ctx.fillStyle = "#64717f";
    ctx.font = "12px Segoe UI, Arial";
    ctx.textAlign = "right";

    for (let i = 0; i <= 4; i += 1) {
        const y = margin.top + chartHeight - (chartHeight * i) / 4;
        const value = (maxValue * i) / 4;
        ctx.beginPath();
        ctx.moveTo(margin.left, y);
        ctx.lineTo(width - margin.right, y);
        ctx.stroke();
        ctx.fillText(formatCompactCurrency(value), margin.left - 8, y + 4);
    }

    const step = visiblePoints.length > 1 ? chartWidth / (visiblePoints.length - 1) : chartWidth;
    const coords = visiblePoints.map((point, index) => ({
        x: margin.left + step * index,
        y: margin.top + chartHeight - (Number(point.value) / maxValue) * chartHeight,
        point,
    }));

    ctx.strokeStyle = options.color || overviewColors.revenue;
    ctx.lineWidth = 3;
    ctx.beginPath();
    coords.forEach((coord, index) => {
        if (index === 0) ctx.moveTo(coord.x, coord.y);
        else ctx.lineTo(coord.x, coord.y);
    });
    ctx.stroke();

    coords.forEach((coord) => {
        ctx.fillStyle = "#ffffff";
        ctx.beginPath();
        ctx.arc(coord.x, coord.y, 5, 0, Math.PI * 2);
        ctx.fill();
        ctx.strokeStyle = options.color || overviewColors.revenue;
        ctx.lineWidth = 2;
        ctx.stroke();
        ctx.fillStyle = "#4a5663";
        ctx.font = "12px Segoe UI, Arial";
        ctx.textAlign = "center";
        ctx.fillText(coord.point.shortLabel || coord.point.label, coord.x, height - 18);
    });
}

function renderOverviewOpsChart() {
    const items = [
        { label: "Sản phẩm", shortLabel: "SP", value: overviewChartState.products, color: overviewColors.product },
        { label: "Nhân viên", shortLabel: "NV", value: overviewChartState.employees, color: overviewColors.employee },
        { label: "Hóa đơn", shortLabel: "HĐ", value: overviewChartState.invoices, color: overviewColors.invoice },
    ];
    drawBarChart("overviewOpsChart", items, { emptyText: "Đang chờ dữ liệu vận hành" });
    setChartLegend("overviewOpsLegend", items);
    setText("overviewOpsChartMeta", activePortal ? activePortal.overviewScopeLabel : "Đang tải");
}

function renderOverviewRevenueChart(stats) {
    if (!activePortal) return;
    const isCentral = activePortal.key === "central";
    if (isCentral) {
        const branches = (stats?.theo_chi_nhanh || []).filter((item) => item.branch_status === "ok");
        const items = branches.map((branch, index) => ({
            label: `${branch.ma_chi_nhanh} - ${branch.ten_chi_nhanh || ""}`.trim(),
            shortLabel: branch.ma_chi_nhanh,
            value: branch.tong_doanh_thu || 0,
            color: index % 2 === 0 ? overviewColors.revenue : "#3867a8",
        }));
        setText("overviewRevenueChartTitle", "Doanh thu theo chi nhánh");
        setText("overviewRevenueChartMeta", `${numberFormatter.format(items.length)} chi nhánh`);
        drawBarChart("overviewRevenueChart", items, {
            emptyText: "Chưa có doanh thu chi nhánh",
            valueFormatter: formatCompactCurrency,
        });
        setChartLegend("overviewRevenueLegend", items);
        return;
    }

    const days = (stats?.theo_ngay || [])
        .slice(0, 7)
        .reverse()
        .map((day) => ({
            label: day.ngay || "",
            shortLabel: String(day.ngay || "").slice(5),
            value: day.tong_doanh_thu || 0,
            color: overviewColors.revenue,
        }));
    setText("overviewRevenueChartTitle", "Doanh thu 7 ngày gần nhất");
    setText("overviewRevenueChartMeta", activePortal.branchCode || "Chi nhánh");
    drawLineChart("overviewRevenueChart", days, {
        emptyText: "Chưa có doanh thu theo ngày",
        color: overviewColors.revenue,
    });
    setChartLegend("overviewRevenueLegend", [{ label: "Doanh thu", color: overviewColors.revenue }]);
}

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
        secondaryLinkHref:
            RUNTIME_CONFIG.secondaryLinkHref ||
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
            currentUser.scope === "central" &&
            ["admin", "giam_doc"].includes(currentUser.chuc_vu)
        );
    }

    return (
        currentUser.scope === "branch" &&
        ["admin", "giam_doc", "truong_phong"].includes(currentUser.chuc_vu)
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
    document.querySelectorAll("[data-branch-only]").forEach((element) => {
        element.hidden = activePortal.key === "central";
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

function canManageProducts() {
    if (!currentUser || !activePortal) return false;
    if (activePortal.key !== "central") return false;
    if (selectedProductSource !== "main") return false;
    return (
        currentUser.scope === "central" &&
        ["admin", "giam_doc", "truong_phong"].includes(currentUser.chuc_vu)
    );
}

function renderProductPaginationBar() {
    const totalPages = Math.max(1, Math.ceil(productListCache.length / PRODUCT_PAGE_SIZE));
    if (productCurrentPage > totalPages) productCurrentPage = totalPages;
    if (productCurrentPage < 1) productCurrentPage = 1;

    const pageInfo = document.getElementById("productPageInfo");
    const prevBtn = document.getElementById("productPrevBtn");
    const nextBtn = document.getElementById("productNextBtn");
    if (pageInfo) {
        pageInfo.textContent = productListCache.length
            ? `Trang ${productCurrentPage} / ${totalPages} — ${numberFormatter.format(productListCache.length)} sản phẩm`
            : "Không có sản phẩm";
    }
    if (prevBtn) prevBtn.disabled = productCurrentPage <= 1;
    if (nextBtn) nextBtn.disabled = productCurrentPage >= totalPages;
}

function renderProducts(payload) {
    const products = payload.data || [];
    productListCache = products;
    productPayloadCache = payload;
    const sourceLabel = getProductSourceLabel(payload);
    const total = payload.pagination ? payload.pagination.total : products.length;
    const canManage = canManageProducts();
    const colCount = canManage ? 7 : 6;

    overviewChartState.products = total;
    renderOverviewOpsChart();
    setText("productCount", numberFormatter.format(total));
    setText("productSource", `Nguồn: ${sourceLabel}`);
    setText("overviewProductSource", sourceLabel);

    if (activePortal.key === "central") {
        setText(
            "branchDbStatus",
            selectedProductSource === "main" ? "DB chính - SQL Server" : sourceLabel
        );
    }

    const actionHead = document.getElementById("productActionHead");
    if (actionHead) actionHead.classList.toggle("hidden", !canManage);

    if (!products.length) {
        renderEmpty("productRows", colCount, "Chưa có dữ liệu sản phẩm.");
        renderProductPaginationBar();
        return;
    }

    const totalPages = Math.max(1, Math.ceil(products.length / PRODUCT_PAGE_SIZE));
    if (productCurrentPage > totalPages) productCurrentPage = totalPages;
    const start = (productCurrentPage - 1) * PRODUCT_PAGE_SIZE;
    const pageProducts = products.slice(start, start + PRODUCT_PAGE_SIZE);

    document.getElementById("productRows").innerHTML = pageProducts
        .map((product) => {
            const actionCell = canManage
                ? `<td class="right">
                        <div class="row-actions">
                            <button class="table-btn" type="button" data-product-action="edit"
                                data-product-id="${escapeHtml(product.ma_sp)}">Sửa</button>
                            <button class="table-btn table-btn-danger" type="button"
                                data-product-action="disable"
                                data-product-id="${escapeHtml(product.ma_sp)}"
                                ${Number(product.trang_thai) === 1 ? "" : "disabled"}>Ngưng</button>
                        </div>
                   </td>`
                : "";
            return `
                <tr>
                    <td>${escapeHtml(product.ma_sp)}</td>
                    <td>${escapeHtml(product.ten_sp)}</td>
                    <td>${escapeHtml(product.ten_loai_sp)}</td>
                    <td>${escapeHtml(product.ten_NCC)}</td>
                    <td class="right">${currencyFormatter.format(product.gia || 0)}</td>
                    <td class="right">${escapeHtml(product.ti_le_giam_gia || 0)}%</td>
                    ${actionCell}
                </tr>
            `;
        })
        .join("");
    renderProductPaginationBar();
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
    overviewChartState.employees = total;
    renderOverviewOpsChart();
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
    overviewChartState.products = 0;
    overviewChartState.employees = 0;
    overviewChartState.invoices = 0;
    overviewChartState.revenueStats = null;
    setText("overviewStatus", "Đang tải");
    setText("overviewOpsChartMeta", "Đang tải");
    setText("overviewRevenueChartMeta", "Đang tải");
    setText("productSource", "Đang tải");
    setText("employeeStatus", "Đang tải");
    setText("secondaryInsightStatus", "Đang tải");
    drawChartEmpty("overviewOpsChart", "Đang tải dữ liệu vận hành");
    drawChartEmpty("overviewRevenueChart", "Đang tải dữ liệu doanh thu");
    employeePageInfo.textContent = "Đang tải phân trang";
    employeePrevBtn.disabled = true;
    employeeNextBtn.disabled = true;

    if (activePortal.key === "central") {
        setText("branchStatus", "Đang tải");
    }
}

function renderApiError(message) {
    setText("overviewStatus", "Lỗi tải dữ liệu");
    setText("overviewOpsChartMeta", "Lỗi tải dữ liệu");
    setText("overviewRevenueChartMeta", "Lỗi tải dữ liệu");
    setText("productSource", "Lỗi tải dữ liệu");
    setText("employeeStatus", "Lỗi tải dữ liệu");
    setText("secondaryInsightStatus", "Lỗi tải dữ liệu");
    drawChartEmpty("overviewOpsChart", message || "Không tải được dữ liệu vận hành");
    drawChartEmpty("overviewRevenueChart", message || "Không tải được dữ liệu doanh thu");
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
        productCurrentPage = 1;
        syncProductSourceButtons();
        switchView("productsView");
        await loadData();
    });
});

document.getElementById("productPrevBtn")?.addEventListener("click", () => {
    if (productCurrentPage > 1) {
        productCurrentPage -= 1;
        renderProducts(productPayloadCache || { data: productListCache });
    }
});
document.getElementById("productNextBtn")?.addEventListener("click", () => {
    const totalPages = Math.max(1, Math.ceil(productListCache.length / PRODUCT_PAGE_SIZE));
    if (productCurrentPage < totalPages) {
        productCurrentPage += 1;
        renderProducts(productPayloadCache || { data: productListCache });
    }
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

// ===== Hóa đơn =====

let selectedInvoiceSource = "all";
let invoiceItems = [];

const invoiceSourceButtons = Array.from(
    document.querySelectorAll("[data-invoice-source]")
);
const invoiceSourcePanel = document.getElementById("invoiceSourcePanel");
const invoiceManageSection = document.getElementById("invoiceManageSection");
const invoiceForm = document.getElementById("invoiceForm");
const invoiceRows = document.getElementById("invoiceRows");
const invoiceItemRows = document.getElementById("invoiceItemRows");
const invoiceFormError = document.getElementById("invoiceFormError");
const invoiceSubmitBtn = document.getElementById("invoiceSubmitBtn");
const invoiceAddItemBtn = document.getElementById("invoiceAddItemBtn");
const invoiceFormTotal = document.getElementById("invoiceFormTotal");
const invoiceDetailSection = document.getElementById("invoiceDetailSection");
const invoiceDetailRows = document.getElementById("invoiceDetailRows");
const invoiceDetailMeta = document.getElementById("invoiceDetailMeta");
const invoiceDetailTitle = document.getElementById("invoiceDetailTitle");
const invoiceDetailClose = document.getElementById("invoiceDetailClose");

function canCreateInvoice() {
    if (!currentUser || !activePortal) return false;
    if (activePortal.key === "central") return false;
    return (
        currentUser.scope === "branch" &&
        ["admin", "giam_doc", "truong_phong", "pho_phong", "nhan_vien"].includes(currentUser.chuc_vu)
    );
}

function syncInvoiceSourceButtons() {
    invoiceSourceButtons.forEach((button) => {
        button.classList.toggle(
            "active",
            button.dataset.invoiceSource === selectedInvoiceSource
        );
    });
}

function getInvoiceListUrl() {
    if (activePortal.key !== "central") {
        return "/api/hoa-don";
    }
    if (selectedInvoiceSource === "all") {
        return "/api/hoa-don";
    }
    return `/api/chi-nhanh/${selectedInvoiceSource}/hoa-don`;
}

function getInvoiceStatsUrl() {
    if (activePortal.key !== "central") {
        return "/api/thong-ke/doanh-thu";
    }
    if (selectedInvoiceSource === "all") {
        return "/api/thong-ke/doanh-thu";
    }
    return `/api/thong-ke/doanh-thu/${selectedInvoiceSource}`;
}

function getInvoiceScopeLabel() {
    if (activePortal.key === "central") {
        return selectedInvoiceSource === "all"
            ? "Toàn hệ thống"
            : selectedInvoiceSource;
    }
    return activePortal.branchCode;
}

function renderInvoiceStats(payload) {
    const isAggregated = activePortal.key === "central" && selectedInvoiceSource === "all";
    let count, revenue, scope;

    if (isAggregated) {
        count = payload?.summary?.so_hoa_don ?? 0;
        revenue = payload?.summary?.tong_doanh_thu ?? 0;
        const okBranches = (payload?.theo_chi_nhanh || []).filter(
            (b) => b.branch_status === "ok"
        ).length;
        scope = `${okBranches} chi nhánh`;
    } else {
        // Branch backend nests under summary; tru_so per-branch flattens. Accept both.
        count = payload?.summary?.so_hoa_don ?? payload?.so_hoa_don ?? 0;
        revenue = payload?.summary?.tong_doanh_thu ?? payload?.tong_doanh_thu ?? 0;
        scope = getInvoiceScopeLabel();
    }

    setText("invoiceCountMetric", numberFormatter.format(count));
    setText("invoiceRevenueMetric", currencyFormatter.format(revenue || 0));
    setText("invoiceScopeMetric", scope);
    setText("invoiceStatsStatus", "Đã đồng bộ");
}

function renderInvoices(payload) {
    let rows = [];
    let total = 0;

    if (Array.isArray(payload)) {
        rows = payload;
        total = rows.length;
    } else if (payload && Array.isArray(payload.data)) {
        rows = payload.data;
        total = payload.total ?? payload.pagination?.total ?? rows.length;
    }

    setText("invoiceListStatus", `${numberFormatter.format(total)} hóa đơn`);

    if (!rows.length) {
        renderEmpty("invoiceRows", 7, "Chưa có hóa đơn.");
        return;
    }

    invoiceRows.innerHTML = rows
        .map((row) => {
            const ma = escapeHtml(row.ma_chi_nhanh || (activePortal.branchCode || ""));
            const ngay = row.ngay_lap ? new Date(row.ngay_lap).toLocaleString("vi-VN") : "";
            const khach = row.ten_kh
                ? `${escapeHtml(row.ten_kh)}${row.sdt_kh ? " · " + escapeHtml(row.sdt_kh) : ""}`
                : "-";
            return `
                <tr>
                    <td>${escapeHtml(row.ma_hd)}</td>
                    <td>${ma}</td>
                    <td>${escapeHtml(ngay)}</td>
                    <td>${khach}</td>
                    <td>${escapeHtml(row.ten_nhan_vien || row.ma_nhan_vien || "")}</td>
                    <td class="right">${currencyFormatter.format(row.tong_tien || 0)}</td>
                    <td class="right">
                        <button class="table-btn" type="button" data-invoice-action="view"
                            data-invoice-id="${escapeHtml(row.ma_hd)}"
                            data-branch="${ma}">Xem</button>
                    </td>
                </tr>
            `;
        })
        .join("");
}

async function loadInvoices() {
    if (!activePortal) return;
    setText("invoiceListStatus", "Đang tải");
    setText("invoiceStatsStatus", "Đang tải");
    setText("invoiceCountMetric", "...");
    setText("invoiceRevenueMetric", "...");
    setText("invoiceScopeMetric", "...");

    try {
        const [list, stats] = await Promise.all([
            fetchJson(getInvoiceListUrl()),
            fetchJson(getInvoiceStatsUrl()),
        ]);
        renderInvoices(list);
        renderInvoiceStats(stats);
    } catch (error) {
        console.error(error);
        if (error.status === 401) {
            clearSession();
            showLogin("Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.");
            return;
        }
        setText("invoiceListStatus", "Lỗi tải dữ liệu");
        setText("invoiceStatsStatus", "Lỗi tải dữ liệu");
        renderEmpty("invoiceRows", 7, "Không tải được hóa đơn.");
    }
}

function _invoiceLineTotal(item) {
    const qty = Number(item.so_luong) || 0;
    const gia = Number(item.don_gia) || 0;
    const disc = Number(item.ti_le_giam_gia) || 0;
    return Math.round(qty * gia * (1 - disc / 100));
}

function renderInvoiceItemRow(index, item) {
    const giamGia = Number(item.ti_le_giam_gia) || 0;
    const lineTotal = _invoiceLineTotal(item);
    return `
        <tr>
            <td>
                <input type="text"
                    list="invoiceSpList"
                    data-invoice-item-field="ma_sp" data-invoice-item-index="${index}"
                    value="${escapeHtml(item.ma_sp)}"
                    placeholder="Gõ mã hoặc tên SP để tìm..."
                    autocomplete="off"
                    style="width:240px;">
            </td>
            <td class="right">
                <input type="number" min="1" step="1" data-invoice-item-field="so_luong" data-invoice-item-index="${index}"
                    value="${escapeHtml(item.so_luong)}" style="text-align:right;width:80px;">
            </td>
            <td class="right">
                <input type="number" data-invoice-item-field="don_gia" data-invoice-item-index="${index}"
                    value="${escapeHtml(item.don_gia)}"
                    readonly tabindex="-1"
                    title="Đơn giá gốc — tự động từ sản phẩm"
                    style="text-align:right;width:130px;background:#f3f5f8;color:#556170;cursor:not-allowed;border-color:#d8dde3;">
            </td>
            <td class="right">
                <input type="number" min="0" max="100" step="0.1"
                    data-invoice-item-field="ti_le_giam_gia" data-invoice-item-index="${index}"
                    value="${giamGia}"
                    readonly tabindex="-1"
                    title="Tỉ lệ giảm giá — tự động từ sản phẩm"
                    style="text-align:right;width:70px;background:#f3f5f8;color:#556170;cursor:not-allowed;border-color:#d8dde3;">
            </td>
            <td class="right">${currencyFormatter.format(lineTotal)}</td>
            <td class="right">
                <button class="table-btn table-btn-danger" type="button" data-invoice-item-remove="${index}">Xóa</button>
            </td>
        </tr>
    `;
}

function renderInvoiceSpDatalist() {
    const datalist = document.getElementById("invoiceSpList");
    if (!datalist) return;
    const sps = Array.isArray(productListCache) ? productListCache : [];
    if (!sps.length) {
        datalist.innerHTML = "";
        return;
    }
    datalist.innerHTML = sps
        .map((sp) => {
            const giaBan = sp.gia_ban_thuc_te || sp.gia || 0;
            const label = `${sp.ten_sp || ""} — ${currencyFormatter.format(giaBan)}`;
            return `<option value="${escapeHtml(sp.ma_sp)}" label="${escapeHtml(label)}">${escapeHtml(label)}</option>`;
        })
        .join("");
}

function renderInvoiceItems() {
    renderInvoiceSpDatalist();
    if (!invoiceItems.length) {
        invoiceItemRows.innerHTML = `<tr><td class="empty" colspan="6">Chưa có sản phẩm. Bấm "+ Thêm dòng" để thêm.</td></tr>`;
    } else {
        invoiceItemRows.innerHTML = invoiceItems.map((it, idx) => renderInvoiceItemRow(idx, it)).join("");
    }
    const total = invoiceItems.reduce((sum, it) => sum + _invoiceLineTotal(it), 0);
    invoiceFormTotal.textContent = currencyFormatter.format(total);
}

function resetInvoiceForm() {
    invoiceForm.reset();
    invoiceItems = [];
    invoiceFormError.textContent = "";
    if (currentUser?.ma_nhan_vien) {
        document.getElementById("invoiceFormEmployee").value = currentUser.ma_nhan_vien;
    }
    renderInvoiceItems();
}

function toggleInvoiceManageVisibility() {
    const visible = canCreateInvoice();
    invoiceManageSection.classList.toggle("hidden", !visible);
    if (invoiceSourcePanel) {
        invoiceSourcePanel.hidden = activePortal.key !== "central";
    }
}

async function showInvoiceDetail(ma_hd, branchCode) {
    let url;
    if (activePortal.key === "central") {
        url = `/api/chi-nhanh/${branchCode || selectedInvoiceSource}/hoa-don/${ma_hd}`;
    } else {
        url = `/api/hoa-don/${ma_hd}`;
    }
    try {
        const detail = await fetchJson(url);
        invoiceDetailSection.classList.remove("hidden");
        invoiceDetailTitle.textContent = `Chi tiết ${detail.ma_hd}`;
        invoiceDetailMeta.innerHTML = `
            <div class="quick-item"><span>Chi nhánh</span><strong>${escapeHtml(detail.ma_chi_nhanh || (activePortal.branchCode || "-"))}</strong></div>
            <div class="quick-item"><span>Ngày lập</span><strong>${escapeHtml(detail.ngay_lap ? new Date(detail.ngay_lap).toLocaleString("vi-VN") : "-")}</strong></div>
            <div class="quick-item"><span>Nhân viên</span><strong>${escapeHtml(detail.ten_nhan_vien || detail.ma_nhan_vien || "-")}</strong></div>
            <div class="quick-item"><span>Khách hàng</span><strong>${escapeHtml(detail.ten_kh || "Khách lẻ")}</strong></div>
            <div class="quick-item"><span>SĐT khách</span><strong>${escapeHtml(detail.sdt_kh || "-")}</strong></div>
            <div class="quick-item"><span>Tổng tiền</span><strong>${currencyFormatter.format(detail.tong_tien || 0)}</strong></div>
        `;
        const items = detail.chi_tiet || [];
        if (!items.length) {
            invoiceDetailRows.innerHTML = `<tr><td class="empty" colspan="5">Chưa có chi tiết.</td></tr>`;
        } else {
            invoiceDetailRows.innerHTML = items
                .map(
                    (it) => `
                        <tr>
                            <td>${escapeHtml(it.ma_sp)}</td>
                            <td>${escapeHtml(it.ten_sp || "")}</td>
                            <td class="right">${numberFormatter.format(it.so_luong || 0)}</td>
                            <td class="right">${currencyFormatter.format(it.don_gia || 0)}</td>
                            <td class="right">${currencyFormatter.format(it.thanh_tien || 0)}</td>
                        </tr>
                    `
                )
                .join("");
        }
        invoiceDetailSection.scrollIntoView({ behavior: "smooth", block: "start" });
    } catch (error) {
        invoiceFormError.textContent = error.message || "Không tải được chi tiết.";
    }
}

invoiceSourceButtons.forEach((button) => {
    button.addEventListener("click", async () => {
        if (activePortal.key !== "central") return;
        const value = button.dataset.invoiceSource;
        if (!value || value === selectedInvoiceSource) return;
        selectedInvoiceSource = value;
        syncInvoiceSourceButtons();
        setText("invoiceSourceStatus", value === "all" ? "Tất cả chi nhánh" : value);
        switchView("invoicesView");
        await loadInvoices();
    });
});

invoiceAddItemBtn.addEventListener("click", () => {
    invoiceItems.push({ ma_sp: "", so_luong: 1, don_gia: 0, ti_le_giam_gia: 0 });
    renderInvoiceItems();
});

invoiceItemRows.addEventListener("input", (event) => {
    const target = event.target;
    const field = target.dataset.invoiceItemField;
    const idx = Number(target.dataset.invoiceItemIndex);
    if (field === undefined || Number.isNaN(idx)) return;

    if (field === "ma_sp") {
        const value = target.value.trim();
        invoiceItems[idx].ma_sp = value;
        // Khi mã SP khớp đúng → auto-fill đơn giá + tỉ lệ giảm giá
        const sps = Array.isArray(productListCache) ? productListCache : [];
        const sp = sps.find((p) => (p.ma_sp || "") === value);
        if (sp) {
            const gia = Number(sp.gia_ban_thuc_te || sp.gia || 0);
            const giamGia = Number(sp.ti_le_giam_gia || 0);
            invoiceItems[idx].don_gia = gia;
            invoiceItems[idx].ti_le_giam_gia = giamGia;
            const priceInput = invoiceItemRows.querySelector(
                `input[data-invoice-item-field="don_gia"][data-invoice-item-index="${idx}"]`
            );
            if (priceInput) priceInput.value = gia;
            const discountInput = invoiceItemRows.querySelector(
                `input[data-invoice-item-field="ti_le_giam_gia"][data-invoice-item-index="${idx}"]`
            );
            if (discountInput) discountInput.value = giamGia;
        }
    } else {
        invoiceItems[idx][field] = Number(target.value) || 0;
    }

    // Cập nhật ô "Thành tiền" của dòng + tổng cộng — không re-render (giữ focus)
    const lineTotal = _invoiceLineTotal(invoiceItems[idx]);
    const tr = target.closest("tr");
    if (tr) {
        const cells = tr.querySelectorAll("td");
        if (cells[4]) cells[4].textContent = currencyFormatter.format(lineTotal);
    }
    const total = invoiceItems.reduce((sum, it) => sum + _invoiceLineTotal(it), 0);
    invoiceFormTotal.textContent = currencyFormatter.format(total);
});

invoiceItemRows.addEventListener("click", (event) => {
    const target = event.target.closest("[data-invoice-item-remove]");
    if (!target) return;
    const idx = Number(target.dataset.invoiceItemRemove);
    if (Number.isNaN(idx)) return;
    invoiceItems.splice(idx, 1);
    renderInvoiceItems();
});

invoiceForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!canCreateInvoice()) return;
    invoiceFormError.textContent = "";
    invoiceSubmitBtn.disabled = true;

    try {
        if (!invoiceItems.length) {
            throw new Error("Hóa đơn phải có ít nhất 1 dòng.");
        }
        const payload = {
            ma_hd: document.getElementById("invoiceFormCode").value.trim(),
            ma_nhan_vien: document.getElementById("invoiceFormEmployee").value.trim(),
            ten_kh: document.getElementById("invoiceFormCustomerName").value.trim() || null,
            sdt_kh: document.getElementById("invoiceFormCustomerPhone").value.trim() || null,
            ghi_chu: document.getElementById("invoiceFormNote").value.trim() || null,
            items: invoiceItems.map((it) => ({
                ma_sp: String(it.ma_sp || "").trim(),
                so_luong: Number(it.so_luong) || 0,
                don_gia: _invoiceLineTotal({ ...it, so_luong: 1 }),
            })),
        };
        await fetchJson("/api/hoa-don", {
            method: "POST",
            body: JSON.stringify(payload),
        });
        resetInvoiceForm();
        await loadInvoices();
        setText("invoiceListStatus", "Đã thêm hóa đơn mới");
    } catch (error) {
        invoiceFormError.textContent = error.message || "Không lưu được hóa đơn.";
    } finally {
        invoiceSubmitBtn.disabled = false;
    }
});

invoiceRows.addEventListener("click", (event) => {
    const button = event.target.closest("[data-invoice-action='view']");
    if (!button) return;
    const ma_hd = button.dataset.invoiceId;
    const branch = button.dataset.branch;
    showInvoiceDetail(ma_hd, branch);
});

invoiceDetailClose.addEventListener("click", () => {
    invoiceDetailSection.classList.add("hidden");
});

async function loadOverviewRevenue() {
    if (!activePortal) return;
    setText("overviewRevenueStatus", "Đang tải");
    setText("overviewInvoiceCount", "...");
    setText("overviewRevenueTotal", "...");
    setText("overviewRevenueExtra", "...");

    try {
        const stats = await fetchJson("/api/thong-ke/doanh-thu");
        renderOverviewRevenue(stats);
    } catch (error) {
        console.error(error);
        if (error.status === 401) {
            clearSession();
            showLogin("Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.");
            return;
        }
        setText("overviewRevenueStatus", "Lỗi tải dữ liệu");
    }
}

function renderOverviewRevenue(stats) {
    if (!activePortal) return;
    const isCentral = activePortal.key === "central";

    // Branch backend nests in `summary`; tru_so aggregated also uses `summary`.
    const summary = stats?.summary || stats || {};
    const count = summary.so_hoa_don ?? 0;
    const revenue = summary.tong_doanh_thu ?? 0;

    overviewChartState.invoices = count;
    overviewChartState.revenueStats = stats;
    renderOverviewOpsChart();
    renderOverviewRevenueChart(stats);
    setText("overviewInvoiceCount", numberFormatter.format(count));
    setText("overviewRevenueTotal", currencyFormatter.format(revenue || 0));

    if (isCentral) {
        const branches = stats?.theo_chi_nhanh || [];
        const top = branches.reduce(
            (best, b) =>
                b.branch_status === "ok" &&
                (best === null || b.tong_doanh_thu > best.tong_doanh_thu)
                    ? b
                    : best,
            null
        );
        setText("overviewRevenueExtraLabel", "Chi nhánh dẫn đầu");
        setText(
            "overviewRevenueExtra",
            top
                ? `${top.ma_chi_nhanh} · ${currencyFormatter.format(top.tong_doanh_thu)}`
                : "Chưa có"
        );

        const tbody = document.getElementById("overviewBranchRevenueRows");
        if (tbody) {
            if (!branches.length) {
                tbody.innerHTML = `<tr><td class="empty" colspan="5">Chưa có dữ liệu chi nhánh.</td></tr>`;
            } else {
                tbody.innerHTML = branches
                    .map((b) => {
                        const statusType = b.branch_status === "ok" ? "ok" : "warn";
                        return `
                            <tr>
                                <td>${escapeHtml(b.ma_chi_nhanh)} · ${escapeHtml(b.ten_chi_nhanh || "")}</td>
                                <td>${badge(formatEngine(b.engine), "muted")}</td>
                                <td>${badge(formatHealthStatus(b.branch_status), statusType)}</td>
                                <td class="right">${numberFormatter.format(b.so_hoa_don || 0)}</td>
                                <td class="right">${currencyFormatter.format(b.tong_doanh_thu || 0)}</td>
                            </tr>
                        `;
                    })
                    .join("");
            }
        }
    } else {
        const days = stats?.theo_ngay || [];
        const best = days.reduce(
            (a, b) => (a === null || b.tong_doanh_thu > a.tong_doanh_thu ? b : a),
            null
        );
        setText("overviewRevenueExtraLabel", "Ngày bán tốt nhất");
        setText(
            "overviewRevenueExtra",
            best && best.tong_doanh_thu
                ? `${best.ngay} · ${currencyFormatter.format(best.tong_doanh_thu)}`
                : "Chưa có"
        );
    }

    setText("overviewRevenueStatus", "Đã đồng bộ");
}

// Hook into existing app lifecycle
const _originalConfigurePortalUI = configurePortalUI;
configurePortalUI = function () {
    _originalConfigurePortalUI();
    selectedInvoiceSource = "all";
    syncInvoiceSourceButtons();
    toggleInvoiceManageVisibility();
    renderInvoiceItems();
    if (invoiceSourcePanel) {
        invoiceSourcePanel.hidden = activePortal.key !== "central";
    }
};

const _originalShowApp = showApp;
showApp = function (user) {
    _originalShowApp(user);
    resetInvoiceForm();
    toggleInvoiceManageVisibility();
};

const _originalLoadCentralData = loadCentralData;
loadCentralData = async function () {
    await _originalLoadCentralData();
    await Promise.all([loadInvoices(), loadOverviewRevenue()]);
};

const _originalLoadBranchData = loadBranchData;
loadBranchData = async function () {
    await _originalLoadBranchData();
    await Promise.all([loadInvoices(), loadOverviewRevenue()]);
};

let overviewChartResizeTimer = null;
window.addEventListener("resize", () => {
    clearTimeout(overviewChartResizeTimer);
    overviewChartResizeTimer = setTimeout(() => {
        renderOverviewOpsChart();
        if (overviewChartState.revenueStats) {
            renderOverviewRevenueChart(overviewChartState.revenueStats);
        }
    }, 120);
});

// ===== Quản lý sản phẩm (chỉ trụ sở, nguồn main) =====

let productFormMode = "create";
let productEditingCode = null;
let productCategoriesCache = null;
let productSuppliersCache = null;

const productManageSection = document.getElementById("productManageSection");
const productForm = document.getElementById("productForm");
const productFormTitle = document.getElementById("productFormTitle");
const productFormError = document.getElementById("productFormError");
const productSubmitBtn = document.getElementById("productSubmitBtn");
const productNewBtn = document.getElementById("productNewBtn");
const productCancelBtn = document.getElementById("productCancelBtn");
const productSyncStatus = document.getElementById("productSyncStatus");
const productRowsEl = document.getElementById("productRows");

function _setOptions(selectEl, items, valueKey, labelKey) {
    if (!selectEl) return;
    const current = selectEl.value;
    selectEl.innerHTML = items
        .map((it) => `<option value="${escapeHtml(it[valueKey])}">${escapeHtml(it[labelKey])} (${escapeHtml(it[valueKey])})</option>`)
        .join("");
    if (current) selectEl.value = current;
}

async function loadProductFormDropdowns() {
    if (!activePortal || activePortal.key !== "central") return;
    if (productCategoriesCache && productSuppliersCache) return;
    try {
        const [cats, sups] = await Promise.all([
            fetchJson("/api/loai-san-pham"),
            fetchJson("/api/nha-cung-cap"),
        ]);
        productCategoriesCache = (cats?.data || cats || []);
        productSuppliersCache = (sups?.data || sups || []);
        _setOptions(
            document.getElementById("productFormCategory"),
            productCategoriesCache,
            "ma_loai_sp",
            "ten_loai_sp"
        );
        _setOptions(
            document.getElementById("productFormSupplier"),
            productSuppliersCache,
            "ma_ncc",
            "ten_ncc"
        );
    } catch (error) {
        console.error("Failed to load product dropdowns", error);
    }
}

function resetProductForm() {
    if (!productForm) return;
    productForm.reset();
    productFormMode = "create";
    productEditingCode = null;
    productFormTitle.textContent = "Thêm sản phẩm mới";
    productSubmitBtn.textContent = "Lưu sản phẩm";
    productFormError.textContent = "";
    productSyncStatus.innerHTML = "";
    const codeInput = document.getElementById("productFormCode");
    if (codeInput) codeInput.disabled = false;
    document.getElementById("productFormStatus").value = "1";
    productCancelBtn.classList.add("hidden");
}

function fillProductForm(product) {
    productFormMode = "edit";
    productEditingCode = product.ma_sp;
    productFormTitle.textContent = `Cập nhật ${product.ma_sp}`;
    productSubmitBtn.textContent = "Cập nhật sản phẩm";
    productFormError.textContent = "";
    productSyncStatus.innerHTML = "";
    productCancelBtn.classList.remove("hidden");

    const codeInput = document.getElementById("productFormCode");
    codeInput.value = product.ma_sp || "";
    codeInput.disabled = true;
    document.getElementById("productFormName").value = product.ten_sp || "";
    document.getElementById("productFormPrice").value = product.gia ?? "";
    document.getElementById("productFormCategory").value = product.ma_loai_sp || "";
    document.getElementById("productFormSupplier").value = product.ma_ncc ?? "";
    document.getElementById("productFormProfit").value = product.ti_le_loi_nhuan ?? "";
    document.getElementById("productFormDiscount").value = product.ti_le_giam_gia ?? "";
    document.getElementById("productFormStatus").value = String(product.trang_thai ?? 1);
    document.getElementById("productFormDesc").value = product.mo_ta || "";

    productManageSection.scrollIntoView({ behavior: "smooth", block: "start" });
}

function collectProductPayload() {
    const get = (id) => document.getElementById(id).value.trim();
    const payload = {
        ten_sp: get("productFormName"),
        gia: Number(get("productFormPrice")),
        ma_loai_sp: get("productFormCategory"),
        ma_ncc: Number(get("productFormSupplier")),
        ti_le_loi_nhuan: Number(get("productFormProfit") || 0),
        ti_le_giam_gia: Number(get("productFormDiscount") || 0),
        mo_ta: get("productFormDesc") || null,
        trang_thai: Number(get("productFormStatus") || "1"),
    };
    if (productFormMode === "create") {
        payload.ma_sp = get("productFormCode");
        if (!payload.ma_sp) throw new Error("Mã sản phẩm là bắt buộc.");
    }
    if (!payload.ten_sp) throw new Error("Tên sản phẩm là bắt buộc.");
    if (!payload.gia || payload.gia <= 0) throw new Error("Giá phải > 0.");
    if (!payload.ma_loai_sp) throw new Error("Loại sản phẩm là bắt buộc.");
    if (!payload.ma_ncc) throw new Error("Nhà cung cấp là bắt buộc.");
    return payload;
}

function renderProductSyncStatus(action, ma_sp) {
    productSyncStatus.innerHTML = `
        <div class="quick-item">
            <span>Đã ${action} ${escapeHtml(ma_sp)}</span>
            <strong>Đang đẩy dữ liệu xuống CN01 + CN02...</strong>
        </div>
    `;
}

function toggleProductManageVisibility() {
    const visible = canManageProducts();
    if (productManageSection) {
        productManageSection.classList.toggle("hidden", !visible);
    }
}

async function submitProductForm(event) {
    event.preventDefault();
    if (!canManageProducts()) return;
    productFormError.textContent = "";
    productSubmitBtn.disabled = true;

    try {
        const payload = collectProductPayload();
        const isCreate = productFormMode === "create";
        const url = isCreate ? "/api/san-pham" : `/api/san-pham/${encodeURIComponent(productEditingCode)}`;
        const method = isCreate ? "POST" : "PUT";
        const saved = await fetchJson(url, {
            method,
            body: JSON.stringify(payload),
        });
        const ma_sp = saved.ma_sp || payload.ma_sp || productEditingCode;
        renderProductSyncStatus(isCreate ? "tạo" : "cập nhật", ma_sp);
        resetProductForm();
        await loadData();
    } catch (error) {
        productFormError.textContent = error.message || "Không lưu được sản phẩm.";
    } finally {
        productSubmitBtn.disabled = false;
    }
}

async function handleProductRowClick(event) {
    const button = event.target.closest("[data-product-action]");
    if (!button || !canManageProducts()) return;
    const ma_sp = button.dataset.productId;
    const action = button.dataset.productAction;
    if (!ma_sp) return;

    if (action === "edit") {
        try {
            const product = await fetchJson(`/api/san-pham/${encodeURIComponent(ma_sp)}`);
            await loadProductFormDropdowns();
            fillProductForm(product);
        } catch (error) {
            productFormError.textContent = error.message || "Không tải được sản phẩm.";
        }
        return;
    }

    if (action === "disable") {
        if (!window.confirm(`Ngưng bán sản phẩm ${ma_sp}? Thay đổi sẽ đẩy xuống cả CN01 và CN02.`)) return;
        try {
            await fetchJson(`/api/san-pham/${encodeURIComponent(ma_sp)}`, { method: "DELETE" });
            renderProductSyncStatus("ngưng", ma_sp);
            if (productEditingCode === ma_sp) resetProductForm();
            await loadData();
        } catch (error) {
            productFormError.textContent = error.message || "Không ngưng được sản phẩm.";
        }
    }
}

if (productForm) productForm.addEventListener("submit", submitProductForm);
if (productNewBtn) productNewBtn.addEventListener("click", async () => {
    resetProductForm();
    await loadProductFormDropdowns();
    switchView("productsView");
});
if (productCancelBtn) productCancelBtn.addEventListener("click", () => resetProductForm());
if (productRowsEl) productRowsEl.addEventListener("click", handleProductRowClick);

// Hook product source changes to toggle manage visibility
productSourceButtons.forEach((button) => {
    button.addEventListener("click", () => {
        // selectedProductSource is updated by the prior listener; defer to next tick
        setTimeout(() => {
            toggleProductManageVisibility();
            if (canManageProducts()) loadProductFormDropdowns();
        }, 0);
    });
});

const _originalConfigurePortalUI_Products = configurePortalUI;
configurePortalUI = function () {
    _originalConfigurePortalUI_Products();
    resetProductForm();
    toggleProductManageVisibility();
    if (canManageProducts()) loadProductFormDropdowns();
};

const _originalShowApp_Products = showApp;
showApp = function (user) {
    _originalShowApp_Products(user);
    toggleProductManageVisibility();
    if (canManageProducts()) loadProductFormDropdowns();
};

// ===== Branch: import SP từ catalog trụ sở =====

const productImportSection = document.getElementById("productImportSection");
const productImportRows = document.getElementById("productImportRows");
const productImportStatus = document.getElementById("productImportStatus");
const productImportRefreshBtn = document.getElementById("productImportRefreshBtn");
const productImportShowAll = document.getElementById("productImportShowAll");
const productImportPageInfo = document.getElementById("productImportPageInfo");
const productImportPrevBtn = document.getElementById("productImportPrevBtn");
const productImportNextBtn = document.getElementById("productImportNextBtn");
let productImportCatalogCache = [];
let productImportPage = 1;
const PRODUCT_IMPORT_PAGE_SIZE = 10;

function canImportFromHQ() {
    if (!currentUser || !activePortal) return false;
    if (activePortal.key === "central") return false;
    return (
        currentUser.scope === "branch" &&
        ["admin", "giam_doc", "truong_phong"].includes(currentUser.chuc_vu)
    );
}

function renderProductImportCatalog() {
    const showAll = productImportShowAll && productImportShowAll.checked;
    const filtered = showAll
        ? productImportCatalogCache
        : productImportCatalogCache.filter((p) => !p.already_imported);

    const totalHq = productImportCatalogCache.length;
    const totalAvailable = productImportCatalogCache.filter((p) => !p.already_imported).length;
    const totalImported = totalHq - totalAvailable;

    const totalPages = Math.max(1, Math.ceil(filtered.length / PRODUCT_IMPORT_PAGE_SIZE));
    if (productImportPage > totalPages) productImportPage = totalPages;
    if (productImportPage < 1) productImportPage = 1;
    const start = (productImportPage - 1) * PRODUCT_IMPORT_PAGE_SIZE;
    const pageRows = filtered.slice(start, start + PRODUCT_IMPORT_PAGE_SIZE);

    if (!filtered.length) {
        const msg = showAll
            ? "Trụ sở chưa có sản phẩm nào."
            : "Chi nhánh đã nhập đủ catalog của trụ sở.";
        productImportRows.innerHTML = `<tr><td class="empty" colspan="7">${msg}</td></tr>`;
    } else {
        productImportRows.innerHTML = pageRows
            .map((p) => {
                const status = p.already_imported
                    ? badge("Đã có ở chi nhánh", "ok")
                    : badge("Chưa nhập", "warn");
                const action = p.already_imported
                    ? `<button class="table-btn" type="button" disabled>Đã có</button>`
                    : `<button class="table-btn" type="button"
                            data-import-action="add"
                            data-import-id="${escapeHtml(p.ma_sp)}">Nhập</button>`;
                return `
                    <tr>
                        <td>${escapeHtml(p.ma_sp)}</td>
                        <td>${escapeHtml(p.ten_sp)}</td>
                        <td>${escapeHtml(p.ten_loai_sp || p.ma_loai_sp || "")}</td>
                        <td>${escapeHtml(p.ten_NCC || p.ten_ncc || ("NCC " + (p.ma_ncc || "")))}</td>
                        <td class="right">${currencyFormatter.format(p.gia || 0)}</td>
                        <td>${status}</td>
                        <td class="right">${action}</td>
                    </tr>
                `;
            })
            .join("");
    }
    if (productImportPageInfo) {
        productImportPageInfo.textContent = filtered.length
            ? `Trang ${productImportPage} / ${totalPages} — ${filtered.length} SP`
            : "Không có dữ liệu";
    }
    if (productImportPrevBtn) productImportPrevBtn.disabled = productImportPage <= 1;
    if (productImportNextBtn) productImportNextBtn.disabled = productImportPage >= totalPages;

    productImportStatus.textContent =
        `Catalog trụ sở: ${totalHq} SP · ${totalImported} đã có ở chi nhánh · ${totalAvailable} có thể nhập.`;
}

async function loadProductImportCatalog() {
    if (!productImportSection || !canImportFromHQ()) return;
    productImportSection.classList.remove("hidden");
    productImportStatus.textContent = "Đang tải catalog từ trụ sở...";
    try {
        const payload = await fetchJson("/api/san-pham/from-hq");
        productImportCatalogCache = payload?.data || [];
        productImportPage = 1;
        renderProductImportCatalog();
    } catch (error) {
        productImportCatalogCache = [];
        productImportRows.innerHTML = `<tr><td class="empty" colspan="7">Không tải được catalog trụ sở.</td></tr>`;
        productImportStatus.textContent = error.message || "Không tải được catalog.";
    }
}

async function handleImportClick(event) {
    const button = event.target.closest("[data-import-action='add']");
    if (!button || !canImportFromHQ()) return;
    const ma_sp = button.dataset.importId;
    if (!ma_sp) return;
    button.disabled = true;
    productImportStatus.textContent = `Đang nhập ${ma_sp}...`;
    try {
        const imported = await fetchJson("/api/san-pham/import-from-hq", {
            method: "POST",
            body: JSON.stringify({ ma_sp }),
        });
        productImportStatus.textContent = `Đã nhập ${imported.ma_sp} · ${imported.ten_sp}`;
        await Promise.all([loadProductImportCatalog(), loadData()]);
    } catch (error) {
        productImportStatus.textContent = error.message || `Không nhập được ${ma_sp}.`;
        button.disabled = false;
    }
}

function toggleProductImportVisibility() {
    if (!productImportSection) return;
    const visible = canImportFromHQ();
    productImportSection.classList.toggle("hidden", !visible);
    if (visible) loadProductImportCatalog();
}

if (productImportRows) productImportRows.addEventListener("click", handleImportClick);
if (productImportRefreshBtn) productImportRefreshBtn.addEventListener("click", loadProductImportCatalog);
if (productImportShowAll) productImportShowAll.addEventListener("change", () => {
    productImportPage = 1;
    renderProductImportCatalog();
});
if (productImportPrevBtn) productImportPrevBtn.addEventListener("click", () => {
    if (productImportPage > 1) {
        productImportPage -= 1;
        renderProductImportCatalog();
    }
});
if (productImportNextBtn) productImportNextBtn.addEventListener("click", () => {
    productImportPage += 1;
    renderProductImportCatalog();
});

const _originalConfigurePortalUI_Import = configurePortalUI;
configurePortalUI = function () {
    _originalConfigurePortalUI_Import();
    toggleProductImportVisibility();
};

const _originalShowApp_Import = showApp;
showApp = function (user) {
    _originalShowApp_Import(user);
    toggleProductImportVisibility();
};

restoreSession();
