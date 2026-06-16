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

// DOM Elements
const navDashboard = document.getElementById("nav-btn-dashboard");
const navClusters = document.getElementById("nav-btn-clusters");
const navReviews = document.getElementById("nav-btn-reviews");
const navLogs = document.getElementById("nav-btn-logs");

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
const stepIngestion = document.getElementById("step-ingestion");
const stepClustering = document.getElementById("step-clustering");
const stepValidation = document.getElementById("step-validation");
const stepDelivery = document.getElementById("step-delivery");

// Detail Modal Elements
const modalRunDetail = document.getElementById("modal-run-detail");
const btnCloseDetail = document.getElementById("btn-close-detail");
const detailWeek = document.getElementById("detail-week");
const detailTime = document.getElementById("detail-time");
const detailIngested = document.getElementById("detail-ingested");
const detailStatus = document.getElementById("detail-status");
const detailThemesList = document.getElementById("detail-themes-list");
const detailJsonBlock = document.getElementById("detail-json-block");

// Reviews Table Elements
const reviewsTableBody = document.getElementById("reviews-table-body");
const reviewsCountBadge = document.getElementById("reviews-count-badge");
const reviewSearchInput = document.getElementById("review-search-input");
const filterPlatform = document.getElementById("filter-platform");
const filterRating = document.getElementById("filter-rating");

// Sidebar & Config Elements
const sidebarDocId = document.getElementById("sidebar-doc-id");
const sidebarMcpUrl = document.getElementById("sidebar-mcp-url");
const configDocId = document.getElementById("config-doc-id");
const configMcpUrl = document.getElementById("config-mcp-url");
const defaultRecipients = document.getElementById("config-default-recipients");
const dashboardTokenBudget = document.getElementById("dashboard-token-budget");
const dashboardLastRun = document.getElementById("dashboard-last-run");
const dashboardLastStatus = document.getElementById("dashboard-last-status");
const dashboardApiConnection = document.getElementById("dashboard-api-connection");

// Metrics Card Elements
const metricTotalReviews = document.getElementById("metric-total-reviews");
const metricTotalClusters = document.getElementById("metric-total-clusters");
const metricNoiseReviews = document.getElementById("metric-noise-reviews");
const metricGqvStatus = document.getElementById("metric-gqv-status");

/* ==========================================================================
   1. Tab Navigation & Title Managers
   ========================================================================== */
function switchTab(activeBtn, targetView, title, subtitle) {
  // Reset navigation items
  [navDashboard, navClusters, navReviews, navLogs].forEach(btn => btn.classList.remove("active"));
  // Reset tab views
  [viewDashboard, viewClusters, viewReviews, viewLogs].forEach(view => view.classList.remove("active"));
  
  // Set active
  activeBtn.classList.add("active");
  targetView.classList.add("active");
  
  // Update Header text
  pageTitle.textContent = title;
  pageSubtitle.textContent = subtitle;
  
  // Load specific tab data
  if (targetView === viewClusters) {
    loadClustersData();
  } else if (targetView === viewReviews) {
    renderReviewsTable();
  } else if (targetView === viewLogs) {
    loadAuditLogs();
  }
}

navDashboard.addEventListener("click", () => {
  switchTab(navDashboard, viewDashboard, "Dashboard Overview", "High-level statistics and recent review ingestion runs.");
});

navClusters.addEventListener("click", () => {
  switchTab(navClusters, viewClusters, "Sentiment Clusters", "Aggregated user feedback pain points and operational recommendations.");
});

navReviews.addEventListener("click", () => {
  switchTab(navReviews, viewReviews, "Review Explorer", "Review search and PII verification data.");
});

navLogs.addEventListener("click", () => {
  switchTab(navLogs, viewLogs, "Audit Log History", "Auditable execution history logs stored on the server.");
});

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
    
    // Server is Online
    dashboardApiConnection.textContent = "Online";
    dashboardApiConnection.className = "text-success";
    
    // Update active configs
    if (data.config) {
      sidebarDocId.textContent = data.config.google_doc_id || "None";
      sidebarMcpUrl.textContent = data.config.google_mcp_server_url || "None";
      configDocId.textContent = data.config.google_doc_id || "None";
      configMcpUrl.textContent = data.config.google_mcp_server_url || "None";
      if (defaultRecipients) {
        defaultRecipients.textContent = data.config.default_recipients || "None";
      }
    }
    
    // Token usage & budget
    dashboardTokenBudget.textContent = `${data.token_usage_today.toLocaleString()} / 70,000`;
    
    // Status Badge & Drawer
    updateStatusBadge(data.status);
    
    // Last Run Info
    if (data.last_run_timestamp) {
      const runDate = new Date(data.last_run_timestamp);
      dashboardLastRun.textContent = runDate.toLocaleString();
      dashboardLastStatus.textContent = data.last_run_status === "completed_success" ? "Success" : "Failed";
      dashboardLastStatus.className = data.last_run_status === "completed_success" ? "text-success" : "text-error";
    }
    
    // Handle status transitions
    if (data.status === "running") {
      runProgressDrawer.style.display = "block";
      updateProgressSteps(data);
      if (!pollingInterval) {
        pollingInterval = setInterval(checkServerStatus, 3000);
      }
    } else {
      if (currentRunStatus === "running" && data.status === "idle") {
        // Just finished running, refresh all data
        refreshAllData();
      }
      runProgressDrawer.style.display = "none";
      if (pollingInterval) {
        clearInterval(pollingInterval);
        pollingInterval = null;
      }
    }
    
    currentRunStatus = data.status;
    
  } catch (error) {
    dashboardApiConnection.textContent = "Offline";
    dashboardApiConnection.className = "text-error";
    updateStatusBadge("offline");
  }
}

function updateStatusBadge(status) {
  statusBadge.className = "badge";
  
  if (status === "idle") {
    statusBadge.classList.add("badge-idle");
    statusBadge.innerHTML = `<span class="status-indicator"></span> Idle`;
  } else if (status === "running") {
    statusBadge.classList.add("badge-running");
    statusBadge.innerHTML = `<span class="status-indicator"></span> Running`;
  } else if (status === "failed") {
    statusBadge.classList.add("badge-failed");
    statusBadge.innerHTML = `<span class="status-indicator"></span> Error`;
  } else {
    statusBadge.classList.add("badge-failed");
    statusBadge.innerHTML = `<span class="status-indicator"></span> Offline`;
  }
}

function updateProgressSteps(data) {
  // Simple step indicator logic based on server runtime estimation
  // (In production, the backend could push progress states, here we simulate based on time/checks)
  stepIngestion.className = "step completed";
  stepClustering.className = "step active";
  stepValidation.className = "step";
  stepDelivery.className = "step";
}

/* ==========================================================================
   3. Loading & Populating Data
   ========================================================================== */
async function refreshAllData() {
  await loadReviewsData();
  await checkServerStatus();
  await loadSummaryStats();
}

async function loadReviewsData() {
  try {
    allReviews = await apiCall("/api/reviews");
    reviewsCountBadge.textContent = `${allReviews.length} Total`;
    renderReviewsTable();
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
      
      // Fetch details of latest run to find noise & GQV status
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
    console.error("Failed loading summary metrics:", err);
  }
}

async function loadClustersData() {
  const accordionList = document.getElementById("clusters-accordion-list");
  accordionList.innerHTML = `<div class="empty-state"><span class="spinner"></span> Loading clusters...</div>`;
  
  try {
    if (allRuns.length === 0) {
      accordionList.innerHTML = `<div class="empty-state"><p>No analysis run history available. Trigger a run to view clusters.</p></div>`;
      return;
    }
    
    // Load latest run details
    const latestRun = allRuns[0];
    const details = await apiCall(`/api/runs/${latestRun.run_id}`);
    
    document.getElementById("clusters-run-week").textContent = `ISO Week: ${details.metadata.iso_week}`;
    
    const themes = details.report?.themes || [];
    if (themes.length === 0) {
      accordionList.innerHTML = `<div class="empty-state"><p>No themes identified in this run.</p></div>`;
      return;
    }
    
    accordionList.innerHTML = "";
    
    themes.forEach((theme, index) => {
      const accItem = document.createElement("div");
      accItem.className = `accordion-item ${index === 0 ? "open" : ""}`;
      
      // Header
      const header = document.createElement("div");
      header.className = "accordion-header";
      header.innerHTML = `
        <span>Theme ${index + 1}: ${escapeHtml(theme.theme_name)}</span>
        <span class="accordion-icon">▼</span>
      `;
      
      // Content
      const content = document.createElement("div");
      content.className = "accordion-content";
      
      // Summary
      const summarySec = document.createElement("div");
      summarySec.className = "accordion-section";
      summarySec.innerHTML = `
        <h4>Summary Analysis</h4>
        <p>${escapeHtml(theme.summary)}</p>
      `;
      
      // Quotes
      const quotesSec = document.createElement("div");
      quotesSec.className = "accordion-section";
      quotesSec.innerHTML = `<h4>Verbatim Customer Feedback</h4>`;
      (theme.quotes || []).forEach(quote => {
        quotesSec.innerHTML += `<blockquote>"${escapeHtml(quote)}"</blockquote>`;
      });
      
      // Actions
      const actionsSec = document.createElement("div");
      actionsSec.className = "accordion-section";
      actionsSec.innerHTML = `<h4>Actionable Product Recommendations</h4>`;
      const recList = document.createElement("ul");
      recList.className = "recommendations-list";
      (theme.action_ideas || []).forEach(idea => {
        recList.innerHTML += `<li>${escapeHtml(idea)}</li>`;
      });
      actionsSec.appendChild(recList);
      
      content.appendChild(summarySec);
      content.appendChild(quotesSec);
      content.appendChild(actionsSec);
      
      accItem.appendChild(header);
      accItem.appendChild(content);
      
      // Accordion Event
      header.addEventListener("click", () => {
        accItem.classList.toggle("open");
      });
      
      accordionList.appendChild(accItem);
    });
    
  } catch (err) {
    accordionList.innerHTML = `<div class="empty-state text-error"><p>Failed to load cluster themes: ${escapeHtml(err.message)}</p></div>`;
  }
}

/* ==========================================================================
   4. Review Explorer Filters & Rendering
   ========================================================================== */
function highlightPii(text) {
  if (!text) return "";
  return text
    .replace(/\[EMAIL\]/g, '<span class="pii-tag">[EMAIL]</span>')
    .replace(/\[PHONE\]/g, '<span class="pii-tag">[PHONE]</span>')
    .replace(/\[ID\]/g, '<span class="pii-tag">[ID]</span>');
}

function renderReviewsTable() {
  reviewsTableBody.innerHTML = "";
  
  const searchVal = reviewSearchInput.value.toLowerCase();
  const platformVal = filterPlatform.value;
  const ratingVal = filterRating.value;
  
  // Filter reviews in memory
  const filtered = allReviews.filter(r => {
    const textMatches = (r.text || "").toLowerCase().includes(searchVal) || (r.author || "").toLowerCase().includes(searchVal);
    const platformMatches = platformVal === "all" || r.platform === platformVal;
    const ratingMatches = ratingVal === "all" || (r.rating !== undefined && r.rating !== null ? r.rating.toString() : "") === ratingVal;
    return textMatches && platformMatches && ratingMatches;
  });
  
  reviewsCountBadge.textContent = `${filtered.length} of ${allReviews.length} shown`;
  
  if (filtered.length === 0) {
    reviewsTableBody.innerHTML = `<tr><td colspan="5" class="text-center text-muted">No matching reviews found.</td></tr>`;
    return;
  }
  
  filtered.forEach(r => {
    const row = document.createElement("tr");
    
    // Format Platform
    const platformIcon = r.platform === "ios" ? "🍎 iOS" : "🤖 Android";
    
    // Format Rating Stars
    const ratingInt = parseInt(r.rating);
    const clampedRating = isNaN(ratingInt) ? 3 : Math.max(1, Math.min(5, ratingInt));
    const stars = "★".repeat(clampedRating) + "☆".repeat(5 - clampedRating);
    
    row.innerHTML = `
      <td><strong>${platformIcon}</strong></td>
      <td><span class="star-rating">${stars}</span></td>
      <td><span class="truncate" style="max-width: 120px; display: inline-block;">${escapeHtml(r.author)}</span></td>
      <td><blockquote>${highlightPii(escapeHtml(r.text))}</blockquote></td>
      <td class="text-muted">${new Date(r.date).toLocaleDateString()}</td>
    `;
    
    reviewsTableBody.appendChild(row);
  });
}

// Bind Review Search Events
reviewSearchInput.addEventListener("input", renderReviewsTable);
filterPlatform.addEventListener("change", renderReviewsTable);
filterRating.addEventListener("change", renderReviewsTable);

/* ==========================================================================
   5. Audit Logs Loading & Details Modal
   ========================================================================== */
async function loadAuditLogs() {
  const tableBody = document.getElementById("logs-table-body");
  tableBody.innerHTML = `<tr><td colspan="7" class="text-center"><span class="spinner"></span> Loading audit runs...</td></tr>`;
  
  try {
    const logs = await apiCall("/api/runs");
    tableBody.innerHTML = "";
    
    if (logs.length === 0) {
      tableBody.innerHTML = `<tr><td colspan="7" class="text-center text-muted">No historical audit logs found.</td></tr>`;
      return;
    }
    
    logs.forEach(run => {
      const row = document.createElement("tr");
      
      const badgeClass = run.status === "completed_success" || run.status === "dry_run_success" ? "badge-completed" : "badge-failed";
      const displayStatus = run.status.replace(/_/g, " ");
      
      row.innerHTML = `
        <td>${new Date(run.timestamp).toLocaleString()}</td>
        <td><strong>${escapeHtml(run.product.toUpperCase())}</strong></td>
        <td><code>${escapeHtml(run.iso_week)}</code></td>
        <td>${run.reviews_ingested} reviews</td>
        <td>${run.total_clusters} clusters</td>
        <td><span class="badge ${badgeClass}">${displayStatus}</span></td>
        <td><button class="btn btn-secondary btn-sm" onclick="showRunDetails('${run.run_id}')">View Details</button></td>
      `;
      
      tableBody.appendChild(row);
    });
  } catch (err) {
    tableBody.innerHTML = `<tr><td colspan="7" class="text-center text-error">Failed to load run logs: ${escapeHtml(err.message)}</td></tr>`;
  }
}

// Expose detail modal trigger globally
window.showRunDetails = async function (runId) {
  try {
    const run = await apiCall(`/api/runs/${runId}`);
    
    detailWeek.textContent = run.metadata.iso_week;
    detailTime.textContent = new Date(run.metadata.timestamp).toLocaleString();
    detailIngested.textContent = `${run.stats.reviews_ingested || 0} reviews`;
    detailStatus.textContent = run.stats.status || "Unknown";
    
    // Fill themes
    detailThemesList.innerHTML = "";
    const themes = run.report?.themes || [];
    if (themes.length === 0) {
      detailThemesList.innerHTML = `<p class="text-muted">No themes generated in this run.</p>`;
    } else {
      themes.forEach(theme => {
        const themeCard = document.createElement("div");
        themeCard.className = "detail-theme-item";
        themeCard.innerHTML = `
          <h5>${escapeHtml(theme.theme_name)}</h5>
          <p class="text-muted" style="font-size: 13px; margin-bottom: 6px;">${escapeHtml(theme.summary)}</p>
          <strong style="font-size: 12px; color: var(--text-muted);">Quotes:</strong>
          <blockquote style="font-size: 12px; margin: 4px 0; border-left: 2px solid var(--primary); padding-left: 8px;">
            "${escapeHtml(theme.quotes?.[0] || 'No quote selected')}"
          </blockquote>
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

/* ==========================================================================
   6. Trigger Run Operations
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

formRunPipeline.addEventListener("submit", async (e) => {
  e.preventDefault();
  modalRunError.style.display = "none";
  
  const product = document.getElementById("input-product").value.trim();
  const windowWeeks = parseInt(document.getElementById("input-window").value);
  const dryRun = document.getElementById("input-dry-run").checked;
  const recipients = document.getElementById("input-recipients").value.trim();
  
  const payload = {
    product: product,
    window_weeks: windowWeeks,
    dry_run: dryRun,
    recipients: recipients || null
  };
  
  try {
    const res = await apiCall("/api/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    
    // Close form modal and open progress drawer
    modalRunPipeline.classList.remove("open");
    runProgressDrawer.style.display = "block";
    
    // Reset steps
    stepIngestion.className = "step active";
    stepClustering.className = "step";
    stepValidation.className = "step";
    stepDelivery.className = "step";
    
    // Start polling status
    checkServerStatus();
    
  } catch (error) {
    modalRunError.textContent = error.message || "Failed to trigger analysis run.";
    modalRunError.style.display = "block";
  }
});

/* ==========================================================================
   7. Helpers & Initialization
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

// Initial Loading
refreshAllData();
setInterval(checkServerStatus, 5000);
