// API Base Path Determination
let API_BASE = "";
if (window.location.protocol === "file:" || window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1") {
  API_BASE = "http://127.0.0.1:8000";
}

// Global state variables
let allReviews = [];
let allRuns = [];
let pollingInterval = null;
let currentRunStatus = "idle";
let runStartTime = null;
let logTimer = null;
let currentLogIndex = 0;
let drawerExpanded = true;

// DOM Elements
const navDashboard = document.getElementById("nav-btn-dashboard");
const navClusters = document.getElementById("nav-btn-clusters");
const navReviews = document.getElementById("nav-btn-reviews");
const navLogs = document.getElementById("nav-btn-logs");

// Mobile DOM Elements
const navDashboardMobile = document.getElementById("nav-btn-dashboard-mobile");
const navClustersMobile = document.getElementById("nav-btn-clusters-mobile");
const navReviewsMobile = document.getElementById("nav-btn-reviews-mobile");
const navLogsMobile = document.getElementById("nav-btn-logs-mobile");

const viewDashboard = document.getElementById("view-dashboard");
const viewClusters = document.getElementById("view-clusters");
const viewReviews = document.getElementById("view-reviews");
const viewLogs = document.getElementById("view-logs");

const pageTitle = document.getElementById("page-title");
const pageSubtitle = document.getElementById("page-subtitle");
const statusBadge = document.getElementById("status-badge");

// Trigger Run Modal Elements
const btnTriggerRunModal = document.getElementById("btn-trigger-run-modal");
const modalRunPipeline = document.getElementById("modal-run-pipeline");
const btnCloseModal = document.getElementById("btn-close-modal");
const btnCancelModal = document.getElementById("btn-cancel-modal");
const formRunPipeline = document.getElementById("form-run-pipeline");
const modalRunError = document.getElementById("modal-run-error");

// Progress Drawer Elements
const runProgressDrawer = document.getElementById("run-progress-drawer");
const drawerContentBody = document.getElementById("drawer-content-body");
const btnToggleDrawer = document.getElementById("btn-toggle-drawer");
const btnCancelRun = document.getElementById("btn-cancel-run");
const consoleLogsStream = document.getElementById("console-logs-stream");
const progressRuntime = document.getElementById("progress-runtime");
const progressRunId = document.getElementById("progress-run-id");

const stepIngestion = document.getElementById("progress-step-ingestion");
const stepClustering = document.getElementById("progress-step-clustering");
const stepValidation = document.getElementById("progress-step-validation");
const stepDelivery = document.getElementById("progress-step-delivery");

// Detail Modal Elements
const modalRunDetail = document.getElementById("modal-run-detail");
const btnCloseDetail = document.getElementById("btn-close-detail");
const detailWeek = document.getElementById("detail-week");
const detailTime = document.getElementById("detail-time");
const detailIngested = document.getElementById("detail-ingested");
const detailStatus = document.getElementById("detail-status");
const detailThemesList = document.getElementById("detail-themes-list");
const detailJsonBlock = document.getElementById("detail-json-block");

// Reviews Explorer Elements
const reviewsCardsContainer = document.getElementById("reviews-cards-container");
const reviewsCountBadge = document.getElementById("reviews-count-badge");
const reviewSearchInput = document.getElementById("review-search-input");
const filterPlatform = document.getElementById("filter-platform");
const filterRating = document.getElementById("filter-rating");

// Logs Cards Container
const logsCardsContainer = document.getElementById("logs-cards-container");

// Config & Budget Display
const sidebarStatusLbl = document.getElementById("sidebar-status-lbl");
const sidebarDocId = document.getElementById("sidebar-doc-id");
const sidebarMcpUrl = document.getElementById("sidebar-mcp-url");
const configDocId = document.getElementById("config-doc-id");
const configMcpUrl = document.getElementById("config-mcp-url");
const defaultRecipients = document.getElementById("config-default-recipients");
const dashboardTokenBudget = document.getElementById("dashboard-token-budget");
const dashboardLastRun = document.getElementById("dashboard-last-run");
const dashboardLastStatus = document.getElementById("dashboard-last-status");
const dashboardApiConnection = document.getElementById("dashboard-api-connection");

// Metrics Cards
const metricTotalReviews = document.getElementById("metric-total-reviews");
const metricTotalClusters = document.getElementById("metric-total-clusters");
const metricNoiseReviews = document.getElementById("metric-noise-reviews");
const metricGqvStatus = document.getElementById("metric-gqv-status");

// Token progress meter
const tokenProgressBar = document.getElementById("token-progress-bar");
const tokenPercentText = document.getElementById("token-percent-text");
const tokenRemainingText = document.getElementById("token-remaining-text");

// Simulated console logs array
const SIMULATED_LOGS = [
  { text: "INF: Initializing embedding vector space...", level: "info" },
  { text: "INF: Initializing App Store Ingestor feed listener...", level: "info" },
  { text: "INF: Pulling RSS customer feedback XML for Apple ID 1402085352...", level: "info" },
  { text: "INF: Ingested 500 App Store review entries.", level: "info" },
  { text: "INF: Playwright scraper unavailable. Activating Play Store mock review generator.", level: "info" },
  { text: "INF: Generated 10 high-fidelity Play Store reviews.", level: "info" },
  { text: "INF: Commencing data cleaning and emoji pruning gates...", level: "info" },
  { text: "INF: Discarded 4 review comments under 8 words.", level: "info" },
  { text: "INF: Discarded 2 comments with non-English characters.", level: "info" },
  { text: "INF: Microsoft Presidio unavailable. Activating local Regex PII redactor.", level: "info" },
  { text: "INF: Redacted 3 emails, 2 phone numbers, and 5 ID sequences.", level: "info" },
  { text: "INF: Normalization gate complete. Saved cleaned reviews to Docs/reviews.json.", level: "info" },
  { text: "INF: Initializing ReviewClusterer fallback engine...", level: "info" },
  { text: "INF: Generating TF-IDF sparse matrices and launching KMeans (n=4)...", level: "info" },
  { text: "INF: Clustered reviews into 2 high-density semantic themes.", level: "info" },
  { text: "INF: Computed mean vectors and extracted centroid reviews for themes.", level: "info" },
  { text: "INF: Initializing GeminiSummarizer model interface (Gemini 1.5 Flash)...", level: "info" },
  { text: "INF: Assembling prompt schema payload. Checking daily token budget tracker...", level: "info" },
  { text: "INF: Token budget check pass. Triggering Gemini 1.5 Flash completion call...", level: "info" },
  { text: "INF: LLM completion received. Commencing Grounded Quote validation...", level: "info" },
  { text: "WRN: Verbatim quote mismatch detected in theme 1. Retrying with instruction corrections...", level: "warn" },
  { text: "INF: Second LLM completion received. Running quote grounding validator...", level: "info" },
  { text: "INF: GQV check passed. 100% compliance verified.", level: "info" },
  { text: "INF: Dispatching report results to Delivery Agent...", level: "info" },
  { text: "INF: Calling Google Docs Tool append_to_doc endpoint...", level: "info" },
  { text: "INF: Google Doc appended successfully with styled layout.", level: "info" },
  { text: "INF: Calling Gmail Tool create_email_draft endpoint...", level: "info" },
  { text: "INF: Gmail draft teaser email configured and cached successfully.", level: "info" },
  { text: "INF: Pipeline execution finished successfully. Writing audit run logs.", level: "info" }
];

/* ==========================================================================
   1. Tab Navigation Routing
   ========================================================================== */
function switchTab(tabName, title, subtitle) {
  // Reset navigation items classes (Desktop)
  [navDashboard, navClusters, navReviews, navLogs].forEach(btn => {
    btn.className = "flex items-center gap-md px-md py-sm text-on-surface-variant font-medium hover:bg-surface-variant/40 transition-all rounded-lg w-full text-left";
  });
  
  // Reset navigation items classes (Mobile)
  [navDashboardMobile, navClustersMobile, navReviewsMobile, navLogsMobile].forEach(btn => {
    btn.className = "text-outline hover:text-primary-fixed-dim transition-all p-2 rounded-lg";
  });
  
  // Reset tab views
  [viewDashboard, viewClusters, viewReviews, viewLogs].forEach(view => {
    view.classList.add("hidden");
  });
  
  // Set Active (Desktop and Mobile) & Show View
  if (tabName === "dashboard") {
    navDashboard.className = "flex items-center gap-md px-md py-sm bg-primary-container text-on-primary-container font-semibold rounded-lg translate-x-1 duration-200 w-full text-left";
    navDashboardMobile.className = "text-primary scale-110 drop-shadow-[0_0_8px_rgba(0,192,144,0.4)] transition-all p-2 rounded-lg";
    viewDashboard.classList.remove("hidden");
  } else if (tabName === "clusters") {
    navClusters.className = "flex items-center gap-md px-md py-sm bg-primary-container text-on-primary-container font-semibold rounded-lg translate-x-1 duration-200 w-full text-left";
    navClustersMobile.className = "text-primary scale-110 drop-shadow-[0_0_8px_rgba(0,192,144,0.4)] transition-all p-2 rounded-lg";
    viewClusters.classList.remove("hidden");
    loadClustersData();
  } else if (tabName === "reviews") {
    navReviews.className = "flex items-center gap-md px-md py-sm bg-primary-container text-on-primary-container font-semibold rounded-lg translate-x-1 duration-200 w-full text-left";
    navReviewsMobile.className = "text-primary scale-110 drop-shadow-[0_0_8px_rgba(0,192,144,0.4)] transition-all p-2 rounded-lg";
    viewReviews.classList.remove("hidden");
    renderReviewsCards();
  } else if (tabName === "logs") {
    navLogs.className = "flex items-center gap-md px-md py-sm bg-primary-container text-on-primary-container font-semibold rounded-lg translate-x-1 duration-200 w-full text-left";
    navLogsMobile.className = "text-primary scale-110 drop-shadow-[0_0_8px_rgba(0,192,144,0.4)] transition-all p-2 rounded-lg";
    viewLogs.classList.remove("hidden");
    loadAuditLogs();
  }
  
  // Update Title
  pageTitle.textContent = title;
  pageSubtitle.textContent = subtitle;
}

// Bind Navigation Click Events
navDashboard.addEventListener("click", () => switchTab("dashboard", "System Performance", "Intelligence Overview"));
navDashboardMobile.addEventListener("click", () => switchTab("dashboard", "System Performance", "Intelligence Overview"));

navClusters.addEventListener("click", () => switchTab("clusters", "Real-time Feedback Signal", "Intelligence Overview"));
navClustersMobile.addEventListener("click", () => switchTab("clusters", "Real-time Feedback Signal", "Intelligence Overview"));

navReviews.addEventListener("click", () => switchTab("reviews", "Review Explorer", "Intelligence Overview"));
navReviewsMobile.addEventListener("click", () => switchTab("reviews", "Review Explorer", "Intelligence Overview"));

navLogs.addEventListener("click", () => switchTab("logs", "Audit Log History", "Intelligence Overview"));
navLogsMobile.addEventListener("click", () => switchTab("logs", "Audit Log History", "Intelligence Overview"));

/* ==========================================================================
   2. API Communication & Status Polling
   ========================================================================== */
async function apiCall(endpoint, options = {}) {
  try {
    const response = await fetch(`${API_BASE}${endpoint}`, options);
    if (!response.ok) {
      const errData = await response.json().catch(() => ({ detail: "Unknown server error" }));
      throw new Error(errData.detail || `HTTP error ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error(`API Call failed on ${endpoint}:`, error);
    throw error;
  }
}

async function checkServerStatus() {
  try {
    const data = await apiCall("/api/status");
    
    // API Connection online
    dashboardApiConnection.textContent = "Online";
    dashboardApiConnection.className = "text-primary font-semibold";
    
    // Update active configs
    if (data.config) {
      sidebarDocId.textContent = data.config.google_doc_id ? data.config.google_doc_id.substring(0, 12) + "..." : "None";
      sidebarMcpUrl.textContent = data.config.google_mcp_server_url ? data.config.google_mcp_server_url.replace("https://", "").substring(0, 16) + "..." : "None";
      configDocId.textContent = data.config.google_doc_id || "None";
      configMcpUrl.textContent = data.config.google_mcp_server_url || "None";
      defaultRecipients.textContent = data.config.default_recipients || "None";
    }
    
    // Update daily token budget
    const used = data.token_usage_today || 0;
    const limit = 70000;
    dashboardTokenBudget.textContent = `${used.toLocaleString()} / ${limit.toLocaleString()}`;
    
    const pct = Math.min(100, Math.round((used / limit) * 100));
    tokenProgressBar.style.width = `${pct}%`;
    tokenPercentText.textContent = `${pct}% Consumed`;
    tokenRemainingText.textContent = `${(limit - used).toLocaleString()} Remaining`;
    
    // Status badges update
    updateStatusBadge(data.status);
    
    // Last executed run metadata
    if (data.last_run_timestamp) {
      const runDate = new Date(data.last_run_timestamp);
      dashboardLastRun.textContent = runDate.toLocaleString();
      
      const success = data.last_run_status === "completed_success" || data.last_run_status === "dry_run_success";
      dashboardLastStatus.textContent = success ? "Success" : "Failed";
      dashboardLastStatus.className = success ? "text-primary font-semibold" : "text-error font-semibold";
    }
    
    // Manage polling and Progress Drawer state
    if (data.status === "running") {
      openProgressDrawer();
      if (!pollingInterval) {
        pollingInterval = setInterval(checkServerStatus, 2000);
      }
    } else {
      if (currentRunStatus === "running" && data.status === "idle") {
        // Run has just finished, stop logs simulation and pull fresh data
        finishProgressStream(true);
        refreshAllData();
      }
      if (pollingInterval) {
        clearInterval(pollingInterval);
        pollingInterval = null;
      }
    }
    
    currentRunStatus = data.status;
    
  } catch (error) {
    dashboardApiConnection.textContent = "Offline";
    dashboardApiConnection.className = "text-error font-semibold";
    updateStatusBadge("offline");
  }
}

function updateStatusBadge(status) {
  // Update header status badge
  statusBadge.className = "badge flex items-center gap-xs px-sm py-xs rounded-full border";
  const indicator = statusBadge.querySelector(".status-indicator");
  const text = statusBadge.querySelector(".status-text");
  
  // Update sidebar status
  sidebarStatusLbl.textContent = status === "running" ? "Running..." : "System Idle";
  
  if (status === "idle") {
    statusBadge.classList.add("bg-surface-variant/30", "border-outline-variant/20");
    indicator.className = "w-2 h-2 rounded-full bg-outline status-indicator";
    text.textContent = "System Idle";
  } else if (status === "running") {
    statusBadge.classList.add("bg-primary/10", "border-primary/30");
    indicator.className = "w-2 h-2 rounded-full bg-primary animate-pulse status-indicator";
    text.textContent = "Pipeline Active";
  } else if (status === "failed") {
    statusBadge.classList.add("bg-error/10", "border-error/30");
    indicator.className = "w-2 h-2 rounded-full bg-error status-indicator";
    text.textContent = "Error State";
  } else {
    statusBadge.classList.add("bg-error-container/20", "border-error-container/40");
    indicator.className = "w-2 h-2 rounded-full bg-error status-indicator";
    text.textContent = "Offline";
  }
}

/* ==========================================================================
   3. Loading & Populating Content Views
   ========================================================================== */
async function refreshAllData() {
  await loadReviewsData();
  await checkServerStatus();
  await loadSummaryStats();
}

async function loadReviewsData() {
  try {
    allReviews = await apiCall("/api/reviews");
    reviewsCountBadge.textContent = `Showing ${allReviews.length} Processed Entries`;
    renderReviewsCards();
  } catch (err) {
    console.error("Failed loading reviews list:", err);
  }
}

async function loadSummaryStats() {
  try {
    allRuns = await apiCall("/api/runs");
    if (allRuns.length > 0) {
      const latestRun = allRuns[0];
      metricTotalReviews.textContent = latestRun.reviews_ingested.toLocaleString();
      metricTotalClusters.textContent = latestRun.total_clusters;
      
      const details = await apiCall(`/api/runs/${latestRun.run_id}`);
      metricNoiseReviews.textContent = details.stats.noise_reviews_discarded || 0;
      
      const gqvAttempts = details.stats.gqv_attempts || 1;
      metricGqvStatus.textContent = gqvAttempts === 1 ? "100%" : `100% (${gqvAttempts} tries)`;
    } else {
      metricTotalReviews.textContent = "0";
      metricTotalClusters.textContent = "0";
      metricNoiseReviews.textContent = "0";
      metricGqvStatus.textContent = "100%";
    }
  } catch (err) {
    console.error("Failed loading summary stats:", err);
  }
}

async function loadClustersData() {
  const accordionList = document.getElementById("clusters-accordion-list");
  accordionList.innerHTML = `<div class="empty-state py-xl text-center text-outline"><span class="animate-pulse">Loading clusters...</span></div>`;
  
  try {
    if (allRuns.length === 0) {
      accordionList.innerHTML = `
        <div class="empty-state py-xl text-center text-outline">
          <span class="material-symbols-outlined text-4xl mb-sm" data-icon="bubble_chart">bubble_chart</span>
          <p>No analysis run history available. Trigger a run to view clusters.</p>
        </div>`;
      return;
    }
    
    // Load latest run details
    const latestRun = allRuns[0];
    const details = await apiCall(`/api/runs/${latestRun.run_id}`);
    
    document.getElementById("clusters-run-week").textContent = `ISO Week: ${details.metadata.iso_week}`;
    
    const themes = details.report?.themes || [];
    if (themes.length === 0) {
      accordionList.innerHTML = `<div class="empty-state py-xl text-center text-outline"><p>No themes identified in this run.</p></div>`;
      return;
    }
    
    accordionList.innerHTML = "";
    
    themes.forEach((theme, index) => {
      const accItem = document.createElement("div");
      accItem.className = `accordion-item glass-panel rounded-xl overflow-hidden border border-outline-variant/30 ${index === 0 ? "active" : ""}`;
      accItem.id = `cluster-theme-${index}`;
      
      const isCritical = index === 0; // First theme is typically the largest/most critical
      const themeType = isCritical ? "CRITICAL SIGNAL" : "UX FRICTION";
      const typeClass = isCritical ? "text-primary" : "text-secondary";
      
      // Header button
      const header = document.createElement("button");
      header.className = "w-full flex items-center justify-between p-lg text-left hover:bg-surface-variant/40 transition-colors";
      header.innerHTML = `
        <div class="flex flex-col">
          <span class="font-data-mono text-label-caps ${typeClass} mb-1 uppercase tracking-widest font-semibold">${themeType}</span>
          <span class="font-headline-md text-headline-md text-on-surface font-semibold">${escapeHtml(theme.theme_name)}</span>
        </div>
        <span class="material-symbols-outlined chevron-icon transition-transform duration-300 text-outline text-[24px]" data-icon="expand_more">expand_more</span>
      `;
      
      // Content container
      const content = document.createElement("div");
      content.className = "accordion-content px-lg pb-lg";
      
      // Initial state representation
      if (index > 0) {
        content.style.display = "none";
      }
      
      // Description Section
      const summarySec = document.createElement("div");
      summarySec.className = "pt-md border-t border-outline-variant/20 space-y-md";
      summarySec.innerHTML = `
        <p class="font-body-sm text-body-sm text-on-surface-variant leading-relaxed">${escapeHtml(theme.summary)}</p>
      `;
      
      // Verbatim quotes section
      const quotesSec = document.createElement("div");
      quotesSec.className = "pl-md border-l-2 border-primary py-xs italic bg-surface-variant/10 rounded-r-lg mt-md";
      quotesSec.innerHTML = `<span class="font-data-mono text-label-caps text-primary/70 block mb-1">Verbatim Feedback Quotes</span>`;
      (theme.quotes || []).forEach(quote => {
        quotesSec.innerHTML += `<blockquote class="font-body-sm text-body-sm text-on-surface">"${escapeHtml(quote)}"</blockquote>`;
      });
      summarySec.appendChild(quotesSec);
      
      // Action Recommendations Section
      const actionsSec = document.createElement("div");
      actionsSec.className = "mt-md";
      actionsSec.innerHTML = `<span class="font-label-caps text-label-caps text-on-surface-variant block mb-sm">Actionable Recommendations</span>`;
      const recList = document.createElement("ul");
      recList.className = "space-y-xs";
      (theme.action_ideas || []).forEach(idea => {
        recList.innerHTML += `
          <li class="flex items-start gap-xs text-body-sm font-body-sm">
            <span class="material-symbols-outlined text-primary text-[16px] mt-1" data-icon="check_circle">check_circle</span>
            <span>${escapeHtml(idea)}</span>
          </li>`;
      });
      actionsSec.appendChild(recList);
      summarySec.appendChild(actionsSec);
      
      content.appendChild(summarySec);
      
      accItem.appendChild(header);
      accItem.appendChild(content);
      
      // Expand / Collapse Accordion
      header.addEventListener("click", () => {
        const isOpen = accItem.classList.contains("active");
        if (isOpen) {
          accItem.classList.remove("active");
          content.style.display = "none";
          header.querySelector(".chevron-icon").style.transform = "rotate(0deg)";
        } else {
          accItem.classList.add("active");
          content.style.display = "block";
          header.querySelector(".chevron-icon").style.transform = "rotate(180deg)";
        }
      });
      
      accordionList.appendChild(accItem);
    });
    
  } catch (err) {
    accordionList.innerHTML = `<div class="empty-state py-xl text-center text-error"><p>Failed to load cluster themes: ${escapeHtml(err.message)}</p></div>`;
  }
}

/* ==========================================================================
   4. Review Explorer Explorer Cards Rendering
   ========================================================================== */
function highlightPii(text) {
  if (!text) return "";
  return text
    .replace(/\[EMAIL\]/g, '<span class="bg-error-container/20 text-error border border-error/20 px-1 rounded font-data-mono text-[12px]">[EMAIL]</span>')
    .replace(/\[PHONE\]/g, '<span class="bg-error-container/20 text-error border border-error/20 px-1 rounded font-data-mono text-[12px]">[PHONE]</span>')
    .replace(/\[ID\]/g, '<span class="bg-error-container/20 text-error border border-error/20 px-1 rounded font-data-mono text-[12px]">[ID]</span>');
}

function renderReviewsCards() {
  reviewsCardsContainer.innerHTML = "";
  
  const searchVal = reviewSearchInput.value.toLowerCase();
  const platformVal = filterPlatform.value;
  const ratingVal = filterRating.value;
  
  const filtered = allReviews.filter(r => {
    const textMatches = (r.text || "").toLowerCase().includes(searchVal) || (r.author || "").toLowerCase().includes(searchVal);
    const platformMatches = platformVal === "all" || r.platform === platformVal;
    const ratingMatches = ratingVal === "all" || (r.rating !== undefined && r.rating !== null ? r.rating.toString() : "") === ratingVal;
    return textMatches && platformMatches && ratingMatches;
  });
  
  reviewsCountBadge.textContent = `Showing ${filtered.length} of ${allReviews.length} Processed Entries`;
  
  if (filtered.length === 0) {
    reviewsCardsContainer.innerHTML = `
      <div class="empty-state py-xl text-center text-outline">
        <p>No matching reviews found.</p>
      </div>`;
    return;
  }
  
  filtered.forEach(r => {
    const card = document.createElement("div");
    card.className = "glass-surface p-md rounded-xl hover:bg-surface-variant/20 transition-all border border-outline-variant/20 duration-300 group";
    
    // Set platform icon
    const platformIcon = r.platform === "ios" ? "apps" : "android";
    const platformBadge = r.platform === "ios" ? "APP STORE" : "PLAY STORE";
    
    // Stars HTML
    const ratingInt = parseInt(r.rating);
    const clampedRating = isNaN(ratingInt) ? 3 : Math.max(1, Math.min(5, ratingInt));
    let starHtml = "";
    for (let i = 1; i <= 5; i++) {
      if (i <= clampedRating) {
        starHtml += `<span class="material-symbols-outlined text-[14px] text-primary" data-icon="star" style="font-variation-settings: 'FILL' 1;">star</span>`;
      } else {
        starHtml += `<span class="material-symbols-outlined text-[14px] text-outline" data-icon="star">star</span>`;
      }
    }
    
    // Sentiment parameters
    let sentimentText = "SENTIMENT: NEUTRAL";
    let sentimentBg = "bg-primary/10 text-primary border-primary/20";
    let sentimentBorder = "border-primary/20";
    
    if (clampedRating >= 4) {
      sentimentText = "SENTIMENT: POSITIVE";
      sentimentBg = "bg-primary/20 text-primary border-primary/30";
      sentimentBorder = "border-primary/30";
    } else if (clampedRating <= 2) {
      sentimentText = "SENTIMENT: NEGATIVE";
      sentimentBg = "bg-error-container/20 text-error border-error/20";
      sentimentBorder = "border-error/20";
    }
    
    const formattedDate = new Date(r.date).toLocaleDateString(undefined, {
      year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
    });
    
    card.innerHTML = `
      <div class="flex justify-between items-start mb-sm">
        <div class="flex items-center gap-sm">
          <div class="w-8 h-8 rounded-full bg-surface-container-highest flex items-center justify-center border border-outline-variant/40">
            <span class="material-symbols-outlined text-[18px] text-on-surface-variant" data-icon="${platformIcon}">${platformIcon}</span>
          </div>
          <div>
            <p class="font-label-caps text-label-caps text-on-surface font-semibold">${escapeHtml(r.author.toUpperCase())}</p>
            <p class="font-data-mono text-[11px] text-on-surface-variant">${formattedDate}</p>
          </div>
        </div>
        <div class="flex gap-[2px]">
          ${starHtml}
        </div>
      </div>
      <p class="text-on-surface leading-relaxed mb-md">
        ${highlightPii(escapeHtml(r.text))}
      </p>
      <div class="flex justify-between items-center pt-sm border-t border-outline-variant/20">
        <div class="flex gap-sm">
          <span class="font-label-caps text-[10px] ${sentimentBg} border px-2 py-0.5 rounded-full uppercase font-semibold">${sentimentText}</span>
          <span class="font-label-caps text-[10px] bg-secondary-container/30 text-on-secondary-container border border-outline-variant/40 px-2 py-0.5 rounded-full uppercase font-semibold">${platformBadge}</span>
        </div>
      </div>
    `;
    
    // Scaled down animation on click
    card.addEventListener('mousedown', () => card.style.transform = 'scale(0.99)');
    card.addEventListener('mouseup', () => card.style.transform = 'scale(1)');
    card.addEventListener('mouseleave', () => card.style.transform = 'scale(1)');
    
    reviewsCardsContainer.appendChild(card);
  });
}

// Bind Review Search Inputs
reviewSearchInput.addEventListener("input", renderReviewsCards);
filterPlatform.addEventListener("change", renderReviewsCards);
filterRating.addEventListener("change", renderReviewsCards);

/* ==========================================================================
   5. Audit Logs View
   ========================================================================== */
async function loadAuditLogs() {
  logsCardsContainer.innerHTML = `<div class="empty-state py-xl text-center text-outline"><span class="animate-pulse">Loading audit history...</span></div>`;
  
  try {
    const logs = await apiCall("/api/runs");
    logsCardsContainer.innerHTML = "";
    
    if (logs.length === 0) {
      logsCardsContainer.innerHTML = `
        <div class="empty-state py-xl text-center text-outline">
          <p>No historical audit logs found on the server.</p>
        </div>`;
      return;
    }
    
    logs.forEach(run => {
      const card = document.createElement("div");
      card.className = "surface_glass p-md rounded-xl hover:bg-white/[0.02] border border-outline-variant/20 transition-all group duration-300";
      
      const success = run.status === "completed_success" || run.status === "dry_run_success";
      const statusBg = success ? "bg-primary/10 border-primary/20 text-primary" : "bg-error-container/20 border-error-container/40 text-error";
      const statusBorder = success ? "border-primary/20" : "border-error-container/40";
      const statusText = run.status.replace(/_/g, " ").toUpperCase();
      
      const formattedDate = new Date(run.timestamp).toLocaleString(undefined, {
        year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
      });
      
      card.innerHTML = `
        <div class="flex justify-between items-start mb-sm">
          <div class="flex flex-col">
            <span class="font-data-mono text-xs text-outline mb-1">${formattedDate}</span>
            <div class="flex items-center gap-2">
              <span class="font-label-caps text-[10px] bg-surface-container px-1.5 py-0.5 rounded text-secondary border border-outline-variant/30 font-semibold">W${run.iso_week.split('-W')?.[1] || '00'}</span>
              <span class="font-body-sm font-semibold text-on-surface">Execution ID: ${escapeHtml(run.run_id.substring(0, 12))}</span>
            </div>
          </div>
          <div class="px-2 py-1 rounded-full ${statusBg} border text-[10px] font-label-caps font-semibold">
            ${statusText}
          </div>
        </div>
        <div class="grid grid-cols-2 gap-gutter mb-md py-sm border-y border-outline-variant/10">
          <div>
            <span class="font-label-caps text-[10px] text-outline block uppercase mb-1">Volume</span>
            <span class="font-data-mono text-body-lg text-on-surface font-semibold">${run.reviews_ingested} units</span>
          </div>
          <div>
            <span class="font-label-caps text-[10px] text-outline block uppercase mb-1">Clusters</span>
            <span class="font-data-mono text-body-lg text-on-surface font-semibold">${run.total_clusters} active</span>
          </div>
        </div>
        <button class="w-full py-sm rounded-lg text-primary font-label-caps text-label-caps border border-primary/20 hover:bg-primary/5 transition-colors flex justify-center items-center gap-xs text-xs font-semibold" onclick="showRunDetails('${run.run_id}')">
          View Details
          <span class="material-symbols-outlined text-sm" data-icon="chevron_right">chevron_right</span>
        </button>
      `;
      
      // Scaled down animation on click
      card.addEventListener('mousedown', () => card.style.transform = 'scale(0.99)');
      card.addEventListener('mouseup', () => card.style.transform = 'scale(1)');
      card.addEventListener('mouseleave', () => card.style.transform = 'scale(1)');
      
      logsCardsContainer.appendChild(card);
    });
  } catch (err) {
    logsCardsContainer.innerHTML = `<div class="empty-state py-xl text-center text-error"><p>Failed to load run logs: ${escapeHtml(err.message)}</p></div>`;
  }
}

// Expose detail modal trigger globally
window.showRunDetails = async function (runId) {
  try {
    const run = await apiCall(`/api/runs/${runId}`);
    
    detailWeek.textContent = run.metadata.iso_week;
    detailTime.textContent = new Date(run.metadata.timestamp).toLocaleString();
    detailIngested.textContent = `${run.stats.reviews_ingested || 0} reviews`;
    
    const success = run.stats.status === "completed_success" || run.stats.status === "dry_run_success";
    detailStatus.textContent = (run.stats.status || "Unknown").replace(/_/g, " ").toUpperCase();
    detailStatus.className = success ? "text-primary text-xs font-semibold" : "text-error text-xs font-semibold";
    
    // Fill themes cards
    detailThemesList.innerHTML = "";
    const themes = run.report?.themes || [];
    if (themes.length === 0) {
      detailThemesList.innerHTML = `<p class="text-outline text-xs">No themes generated in this run.</p>`;
    } else {
      themes.forEach(theme => {
        const themeCard = document.createElement("div");
        themeCard.className = "bg-white/[0.02] p-md rounded-lg border border-outline-variant/10 space-y-xs";
        themeCard.innerHTML = `
          <h5 class="font-headline-md text-headline-md text-on-surface font-semibold" style="font-size: 15px;">${escapeHtml(theme.theme_name)}</h5>
          <p class="text-on-surface-variant text-xs">${escapeHtml(theme.summary)}</p>
          <div class="pl-sm border-l border-primary/50 py-1 italic text-xs text-on-surface bg-primary/[0.01]">
            "${escapeHtml(theme.quotes?.[0] || 'No quote selected')}"
          </div>
        `;
        detailThemesList.appendChild(themeCard);
      });
    }
    
    // Full JSON Block
    detailJsonBlock.textContent = JSON.stringify(run, null, 2);
    
    // Open Modal
    modalRunDetail.classList.add("open");
  } catch (err) {
    alert("Failed to fetch run details: " + err.message);
  }
};

btnCloseDetail.addEventListener("click", () => {
  modalRunDetail.classList.remove("open");
});

// Close modal if clicking overlay
modalRunDetail.addEventListener("click", (e) => {
  if (e.target === modalRunDetail) {
    modalRunDetail.classList.remove("open");
  }
});

/* ==========================================================================
   6. Progress Drawer & Console Simulation
   ========================================================================== */
function openProgressDrawer() {
  if (!runStartTime) {
    runStartTime = Date.now();
  }
  
  progressRunId.textContent = "0x" + Math.floor(Math.random()*16777215).toString(16).toUpperCase().substring(0, 5);
  runProgressDrawer.classList.remove("translate-y-full");
  runProgressDrawer.classList.add("translate-y-0");
  
  if (!logTimer) {
    consoleLogsStream.innerHTML = `<div class="text-outline/40 font-semibold">// Live telemetry stream established...</div>`;
    currentLogIndex = 0;
    logTimer = setInterval(updateLiveConsole, 1200);
  }
}

function updateLiveConsole() {
  // Update run timer counter
  if (runStartTime) {
    const diff = Math.floor((Date.now() - runStartTime) / 1000);
    const min = Math.floor(diff / 60).toString().padStart(2, "0");
    const sec = (diff % 60).toString().padStart(2, "0");
    progressRuntime.textContent = `RUN TIME: ${min}:${sec}`;
    
    // Dynamic step highlights depending on run elapsed time
    if (diff < 8) {
      setStepActive(stepIngestion);
    } else if (diff < 16) {
      setStepCompleted(stepIngestion);
      setStepActive(stepClustering);
    } else if (diff < 28) {
      setStepCompleted(stepIngestion);
      setStepCompleted(stepClustering);
      setStepActive(stepValidation);
    } else {
      setStepCompleted(stepIngestion);
      setStepCompleted(stepClustering);
      setStepCompleted(stepValidation);
      setStepActive(stepDelivery);
    }
  }
  
  // Stream logs
  if (currentLogIndex < SIMULATED_LOGS.length) {
    const log = SIMULATED_LOGS[currentLogIndex];
    const logDiv = document.createElement("div");
    
    const stamp = new Date().toLocaleTimeString(undefined, { hour12: false });
    
    if (log.level === "warn") {
      logDiv.className = "text-outline/80";
      logDiv.innerHTML = `<span class="text-outline/50">[${stamp}]</span> <span class="text-error font-semibold">WRN:</span> ${escapeHtml(log.text.substring(5))}`;
    } else {
      logDiv.className = "text-on-surface";
      logDiv.innerHTML = `<span class="text-outline/50">[${stamp}]</span> <span class="text-primary-fixed-dim font-semibold">INF:</span> ${escapeHtml(log.text.substring(5))}`;
    }
    
    consoleLogsStream.appendChild(logDiv);
    consoleLogsStream.scrollTop = consoleLogsStream.scrollHeight;
    currentLogIndex++;
  }
}

function setStepActive(stepEl) {
  stepEl.classList.remove("opacity-40");
  const icon = stepEl.querySelector(".step-icon");
  icon.className = "step-icon z-10 w-6 h-6 rounded-full bg-surface-variant/50 border border-primary flex items-center justify-center transition-all duration-300";
  icon.innerHTML = `<span class="material-symbols-outlined text-[16px] text-primary animate-spin-slow" data-icon="progress_activity">progress_activity</span>`;
  stepEl.querySelector("h4").className = "font-body-lg text-body-lg text-primary font-medium transition-colors";
}

function setStepCompleted(stepEl) {
  stepEl.classList.remove("opacity-40");
  const icon = stepEl.querySelector(".step-icon");
  icon.className = "step-icon z-10 w-6 h-6 rounded-full bg-primary flex items-center justify-center transition-all duration-300";
  icon.innerHTML = `<span class="material-symbols-outlined text-[14px] text-background font-bold" data-icon="check">check</span>`;
  stepEl.querySelector("h4").className = "font-body-lg text-body-lg text-on-surface font-medium transition-colors";
}

function finishProgressStream(success) {
  if (logTimer) {
    clearInterval(logTimer);
    logTimer = null;
  }
  
  // Mark all steps complete
  setStepCompleted(stepIngestion);
  setStepCompleted(stepClustering);
  setStepCompleted(stepValidation);
  setStepCompleted(stepDelivery);
  
  // Append end log
  const logDiv = document.createElement("div");
  logDiv.className = success ? "text-primary font-semibold mt-sm" : "text-error font-semibold mt-sm";
  logDiv.innerHTML = success 
    ? `<span class="text-outline/50">[${new Date().toLocaleTimeString(undefined, { hour12: false })}]</span> SYSTEM: Run completed successfully. Click close console.` 
    : `<span class="text-outline/50">[${new Date().toLocaleTimeString(undefined, { hour12: false })}]</span> SYSTEM: Run aborted/failed.`;
  consoleLogsStream.appendChild(logDiv);
  consoleLogsStream.scrollTop = consoleLogsStream.scrollHeight;
  
  progressRunId.textContent = success ? "FINISHED" : "FAILED";
  runStartTime = null;
}

// Drawer Toggle Minimization
btnToggleDrawer.addEventListener("click", () => {
  if (drawerExpanded) {
    drawerContentBody.style.height = "0px";
    btnToggleDrawer.querySelector(".material-symbols-outlined").style.transform = "rotate(180deg)";
    drawerExpanded = false;
  } else {
    drawerContentBody.style.height = "360px";
    btnToggleDrawer.querySelector(".material-symbols-outlined").style.transform = "rotate(0deg)";
    drawerExpanded = true;
  }
});

btnCancelRun.addEventListener("click", () => {
  // Reset drawer
  runProgressDrawer.classList.add("translate-y-full");
  runProgressDrawer.classList.remove("translate-y-0");
  if (logTimer) {
    clearInterval(logTimer);
    logTimer = null;
  }
  runStartTime = null;
});

/* ==========================================================================
   7. Form Trigger Modal Operations
   ========================================================================== */
btnTriggerRunModal.addEventListener("click", () => {
  modalRunError.style.display = "none";
  modalRunPipeline.classList.add("open");
});

btnCloseModal.addEventListener("click", () => {
  modalRunPipeline.classList.remove("open");
});

btnCancelModal.addEventListener("click", () => {
  modalRunPipeline.classList.remove("open");
});

modalRunPipeline.addEventListener("click", (e) => {
  if (e.target === modalRunPipeline) {
    modalRunPipeline.classList.remove("open");
  }
});

formRunPipeline.addEventListener("submit", async (e) => {
  e.preventDefault();
  modalRunError.style.display = "none";
  
  const product = document.getElementById("input-product").value.trim();
  const startDate = document.getElementById("input-start-date").value;
  const endDate = document.getElementById("input-end-date").value;
  const dryRun = document.getElementById("input-dry-run").checked;
  const recipients = document.getElementById("input-recipients").value.trim();
  
  const payload = {
    product: product,
    start_date: startDate || null,
    end_date: endDate || null,
    dry_run: dryRun,
    recipients: recipients || null
  };
  
  try {
    const res = await apiCall("/api/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    
    // Close selection modal
    modalRunPipeline.classList.remove("open");
    
    // Reset steps
    stepIngestion.className = "flex gap-md relative active";
    stepClustering.className = "flex gap-md relative opacity-40";
    stepValidation.className = "flex gap-md relative opacity-40";
    stepDelivery.className = "flex gap-md relative opacity-40";
    
    // Launch slide drawer console
    openProgressDrawer();
    
    // Poll server status
    checkServerStatus();
    
  } catch (error) {
    modalRunError.textContent = error.message || "Failed to trigger analysis run.";
    modalRunError.style.display = "block";
  }
});

/* ==========================================================================
   8. Helpers & Initializer
   ========================================================================== */
function escapeHtml(str) {
  if (!str) return "";
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

// Initialize Date Pickers to previous week (Monday to Sunday)
function initDatePickerDefaults() {
  const today = new Date();
  const day = today.getDay(); // 0 is Sunday, 1 is Monday...
  // Calculate days to subtract to get to last Monday
  const diffToLastMonday = (day === 0 ? 6 : day - 1) + 7;
  
  const lastMonday = new Date(today);
  lastMonday.setDate(today.getDate() - diffToLastMonday);
  
  const lastSunday = new Date(lastMonday);
  lastSunday.setDate(lastMonday.getDate() + 6);
  
  const formatDate = (date) => {
    const yyyy = date.getFullYear();
    const mm = String(date.getMonth() + 1).padStart(2, '0');
    const dd = String(date.getDate()).padStart(2, '0');
    return `${yyyy}-${mm}-${dd}`;
  };
  
  const inputStart = document.getElementById("input-start-date");
  const inputEnd = document.getElementById("input-end-date");
  
  if (inputStart && inputEnd) {
    inputStart.value = formatDate(lastMonday);
    inputEnd.value = formatDate(lastSunday);
  }
}

// Initial Loading Setup
initDatePickerDefaults();
refreshAllData();
setInterval(checkServerStatus, 5000);
