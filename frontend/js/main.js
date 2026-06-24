const API = 'http://localhost:3000'
const gc = '#e5e9f0', tc = '#8a96a8'

// ── Mock Data (Fallback when backend is not available) ────────────────────

const MOCK_DATA = {
  dashboard: {
    invoices_today: 47,
    flags_raised: 12,
    high_risk: 5,
    capital_at_risk: 425000,
    compliance_rate: 78.5,
    top_vendors_at_risk: [
      { vendor: 'Matahari Trading Sdn Bhd', amount: 128000, level: 'high' },
      { vendor: 'Kencana Engineering (M) Sdn Bhd', amount: 95000, level: 'high' },
      { vendor: 'Sentosa Supplies Sdn Bhd', amount: 72000, level: 'minor' },
      { vendor: 'Bina Jaya Construction Sdn Bhd', amount: 55000, level: 'minor' },
      { vendor: 'Tropical Food Industries Sdn Bhd', amount: 48000, level: 'high' },
    ],
    weekly_trend: [
      { week: 'Week 1', clean: 28, minor: 8, high_risk: 4 },
      { week: 'Week 2', clean: 32, minor: 6, high_risk: 3 },
      { week: 'Week 3', clean: 25, minor: 10, high_risk: 5 },
      { week: 'Week 4', clean: 30, minor: 7, high_risk: 4 },
      { week: 'Week 5', clean: 35, minor: 5, high_risk: 2 },
      { week: 'Week 6', clean: 38, minor: 4, high_risk: 3 },
    ],
    discrepancy_types: [
      { type: 'SST rate', count: 15 },
      { type: 'Entity name', count: 10 },
      { type: 'Tax code', count: 8 },
      { type: 'Rounding', count: 5 },
    ]
  },
  invoices: [
    { id: 'INV-001', vendor: 'Matahari Trading Sdn Bhd', invoice_no: 'MT-2026-0891', amount: 128000, sst_rate: '8%', lhdn_status: 'pending', agent_status: 'high_risk', flag_type: 'Entity name mismatch', risk_score: 8.5 },
    { id: 'INV-002', vendor: 'Kencana Engineering', invoice_no: 'KE-2026-0452', amount: 95000, sst_rate: '6%', lhdn_status: 'rejected', agent_status: 'high_risk', flag_type: 'SST rate mismatch', risk_score: 7.8 },
    { id: 'INV-003', vendor: 'Sentosa Supplies', invoice_no: 'SS-2026-0123', amount: 72000, sst_rate: '8%', lhdn_status: 'validated', agent_status: 'minor_flag', flag_type: 'Address mismatch', risk_score: 4.5 },
    { id: 'INV-004', vendor: 'Bina Jaya Construction', invoice_no: 'BJ-2026-0789', amount: 55000, sst_rate: '0%', lhdn_status: 'validated', agent_status: 'minor_flag', flag_type: 'Rounding discrepancy', risk_score: 3.2 },
    { id: 'INV-005', vendor: 'Tropical Food Industries', invoice_no: 'TF-2026-0345', amount: 48000, sst_rate: '8%', lhdn_status: 'pending', agent_status: 'high_risk', flag_type: 'Registration number missing', risk_score: 7.1 },
    { id: 'INV-006', vendor: 'Sinar Jaya Manufacturing', invoice_no: 'SJ-2026-0567', amount: 32000, sst_rate: '8%', lhdn_status: 'validated', agent_status: 'clean', flag_type: null, risk_score: 1.2 },
    { id: 'INV-007', vendor: 'Kuala Lumpur Trading Co.', invoice_no: 'KL-2026-0234', amount: 28000, sst_rate: '6%', lhdn_status: 'validated', agent_status: 'clean', flag_type: null, risk_score: 0.8 },
    { id: 'INV-008', vendor: 'Palm Oil Refinery Sdn Bhd', invoice_no: 'PO-2026-0678', amount: 150000, sst_rate: '8%', lhdn_status: 'rejected', agent_status: 'high_risk', flag_type: 'SST rate mismatch', risk_score: 9.0 },
  ],
  comms: [
    { date: '2026-06-23 14:30', invoice: 'INV-001', vendor: 'Matahari Trading', type: 'Resolution', sent: true, response: 'awaiting' },
    { date: '2026-06-22 10:15', invoice: 'INV-002', vendor: 'Kencana Engineering', type: 'Follow-up', sent: true, response: 'resolved' },
    { date: '2026-06-21 16:45', invoice: 'INV-003', vendor: 'Sentosa Supplies', type: 'Resolution', sent: false, response: 'pending' },
  ],
  analytics: {
    compliance_rate_mtd: 78.5,
    avg_resolution_days: 2.4,
    sst_recovered: 45600,
    lhdn_rejections_avoided: 8,
    monthly_trend: [
      { month: 'Jan', rate: 72 },
      { month: 'Feb', rate: 75 },
      { month: 'Mar', rate: 78 },
      { month: 'Apr', rate: 76 },
      { month: 'May', rate: 80 },
      { month: 'Jun', rate: 83 },
    ]
  },
  audit: {
    logs: [
      { timestamp: '2026-06-24 09:30:15', agent: 'ai_agent', invoice: 'INV-001', action: 'process_invoice', result: 'high_risk', result_label: 'High-risk flagged' },
      { timestamp: '2026-06-24 08:45:22', agent: 'ai_agent', invoice: 'INV-002', action: 'validate_lhdn', result: 'warning', result_label: 'Mismatch' },
      { timestamp: '2026-06-24 08:12:07', agent: 'user', invoice: 'INV-003', action: 'approve', result: 'ok', result_label: 'OK' },
      { timestamp: '2026-06-23 17:30:45', agent: 'ai_agent', invoice: 'INV-004', action: 'process_invoice', result: 'ok', result_label: 'OK' },
      { timestamp: '2026-06-23 16:20:33', agent: 'ai_agent', invoice: 'INV-005', action: 'validate_lhdn', result: 'high_risk', result_label: 'High-risk flagged' },
    ],
    total: 5
  }
}

// ── Helper function to fetch with fallback ─────────────────────────────────

async function fetchWithFallback(url, fallbackData) {
  try {
    const response = await fetch(url)
    if (!response.ok) throw new Error('Network response was not ok')
    const data = await response.json()
    return data
  } catch (error) {
    console.warn('Using fallback data for ' + url, error.message)
    return fallbackData
  }
}

// ── Navigation ────────────────────────────────────────────────────────────────

function nav(id, el) {
  document.querySelectorAll('.page').forEach(function(p) { p.classList.remove('active') })
  document.querySelectorAll('.nav-item').forEach(function(n) { n.classList.remove('active') })
  document.getElementById('page-' + id).classList.add('active')
  if (el) el.classList.add('active')
  
  var loaders = { 
    dashboard: loadDashboard, 
    queue: loadQueue, 
    analytics: loadAnalytics, 
    auditlog: loadAuditLog, 
    discrepancy: loadDiscrepancies, 
    comms: loadComms 
  }
  if (loaders[id]) loaders[id]()
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function rm(v, t) {
  t = t || 'danger'
  return '<span class="badge badge-' + t + '">' + v + '</span>'
}

function fmt(n) {
  return Number(n).toLocaleString('en-MY', {minimumFractionDigits:2, maximumFractionDigits:2})
}

function agentBadge(s, flag) {
  if (s === 'high_risk') return rm(flag || 'High-risk')
  if (s === 'minor_flag') return rm(flag || 'Minor flag', 'warning')
  return rm('Clean', 'success')
}

function lhdnBadge(s) {
  if (s === 'validated') return rm('Validated', 'success')
  if (s === 'rejected') return rm('Rejected')
  return rm('Pending', 'warning')
}

function capitalizeFirst(str) {
  if (!str) return ''
  return str.charAt(0).toUpperCase() + str.slice(1)
}

// ── DASHBOARD ─────────────────────────────────────────────────────────────────

var dashChartInst

async function loadDashboard() {
  var fallback = MOCK_DATA.dashboard
  var d = await fetchWithFallback(API + '/api/dashboard', fallback)
  
  document.getElementById('dash-sub').textContent = 'Real-time status — LHDN MyInvois | Compliance: ' + d.compliance_rate + '%'
  document.getElementById('m-total').textContent = d.invoices_today
  document.getElementById('m-flags').textContent = d.flags_raised
  document.getElementById('m-high').textContent = d.high_risk
  document.getElementById('m-capital').textContent = 'RM ' + fmt(d.capital_at_risk)
  document.getElementById('dash-flag-count').textContent = d.high_risk + ' unresolved'
  
  var tb = document.getElementById('dash-flags-tbody')
  var filtered = d.top_vendors_at_risk.filter(function(v) { return v.amount > 0 }).slice(0,5)
  if (filtered.length > 0) {
    tb.innerHTML = filtered.map(function(v) {
      return '<tr><td><strong>' + v.vendor + '</strong></td>' +
        '<td>' + rm(v.level === 'high' ? 'High-risk' : 'Minor flag', v.level === 'high' ? 'danger' : 'warning') + '</td>' +
        '<td style="color:var(--' + (v.level === 'high' ? 'red' : 'amber') + ');font-weight:500">RM ' + fmt(v.amount) + '</td></tr>'
    }).join('')
  } else {
    tb.innerHTML = '<tr><td colspan="3" style="text-align:center;color:var(--muted)">No flags found</td></tr>'
  }
  
  var clean = d.invoices_today - d.flags_raised
  var minor = d.flags_raised - d.high_risk
  if (dashChartInst) dashChartInst.destroy()
  dashChartInst = new Chart(document.getElementById('dashChart'), {
    type: 'doughnut',
    data: { labels: ['Clean', 'Minor flag', 'High-risk'], datasets: [{ data: [clean, minor, d.high_risk], backgroundColor: ['#378ADD', '#EF9F27', '#E24B4A'], borderWidth: 0 }] },
    options: { responsive: true, maintainAspectRatio: false, cutout: '70%', plugins: { legend: { display: false } } }
  })
}

// ── INVOICE QUEUE ─────────────────────────────────────────────────────────────

var allInvoices = []
var qFilter = 'all'

async function loadQueue() {
  var fallback = { invoices: MOCK_DATA.invoices }
  var d = await fetchWithFallback(API + '/api/invoices', fallback)
  allInvoices = d.invoices || []
  renderQueue()
}

function filterQueue(f, el) {
  qFilter = f
  document.querySelectorAll('.filter-btn').forEach(function(b) { b.classList.remove('active') })
  el.classList.add('active')
  renderQueue()
}

function renderQueue() {
  var list = qFilter === 'all' ? allInvoices : allInvoices.filter(function(i) { return i.agent_status === qFilter })
  document.getElementById('queue-count').textContent = list.length + ' invoices'
  if (list.length > 0) {
    document.getElementById('queue-tbody').innerHTML = list.map(function(inv) {
      var riskColor = inv.risk_score > 7 ? 'var(--red)' : inv.risk_score > 4 ? '#EF9F27' : 'var(--green)'
      var reviewBtn = inv.agent_status !== 'clean' ? '<button class="btn primary" onclick="goDisc(\'' + inv.id + '\')">Review →</button>' : ''
      return '<tr>' +
        '<td style="color:var(--muted);font-size:11px">' + inv.id + '</td>' +
        '<td><strong>' + inv.vendor + '</strong></td>' +
        '<td style="font-family:monospace;font-size:12px">' + inv.invoice_no + '</td>' +
        '<td>' + fmt(inv.amount) + '</td>' +
        '<td>' + inv.sst_rate + '</td>' +
        '<td>' + lhdnBadge(inv.lhdn_status) + '</td>' +
        '<td>' + agentBadge(inv.agent_status, inv.flag_type) + '</td>' +
        '<td>' +
          '<div style="font-size:11px;color:var(--muted);margin-bottom:2px">' + (inv.risk_score || 0).toFixed(1) + '/10</div>' +
          '<div style="width:56px;height:4px;background:#edf1f7;border-radius:2px;overflow:hidden">' +
            '<div style="width:' + (inv.risk_score || 0) * 10 + '%;height:100%;background:' + riskColor + '"></div>' +
          '</div>' +
        '</td>' +
        '<td>' + reviewBtn + '</td>' +
      '</tr>'
    }).join('')
  } else {
    document.getElementById('queue-tbody').innerHTML = '<tr><td colspan="9" style="text-align:center;color:var(--muted)">No invoices found</td></tr>'
  }
}

function goDisc(id) {
  nav('discrepancy', document.querySelector('.nav-item[onclick*="discrepancy"]'))
  showDiscDetail(id)
}

// ── DISCREPANCIES ─────────────────────────────────────────────────────────────

var discData = {}

async function loadDiscrepancies() {
  var fallback = { discrepancies: MOCK_DATA.invoices.filter(function(i) { return i.agent_status !== 'clean' }) }
  var d = await fetchWithFallback(API + '/api/discrepancies', fallback)
  var list = d.discrepancies || []
  
  if (list.length > 0) {
    document.getElementById('disc-list').innerHTML = list.map(function(inv) {
      return '<div onclick="showDiscDetail(\'' + inv.id + '\')" style="padding:10px 16px;cursor:pointer;border-left:3px solid transparent" id="dl-' + inv.id + '">' +
        '<div style="font-size:13px;font-weight:500">' + inv.id + '</div>' +
        '<div style="font-size:11px;color:var(--muted);margin-top:1px">' + (inv.vendor || '').split(' ').slice(0,2).join(' ') + '</div>' +
        '<div style="margin-top:4px">' + rm((inv.risk_score || 0).toFixed(1) + ' risk', inv.agent_status === 'high_risk' ? 'danger' : 'warning') + '</div>' +
      '</div>'
    }).join('')
    showDiscDetail(list[0].id)
  } else {
    document.getElementById('disc-list').innerHTML = '<div style="padding:16px;text-align:center;color:var(--muted)">No discrepancies found</div>'
  }
}

async function showDiscDetail(id) {
  document.querySelectorAll('#disc-list > div').forEach(function(el) {
    el.style.borderLeftColor = 'transparent'
    el.style.background = 'transparent'
  })
  var el = document.getElementById('dl-' + id)
  if (el) {
    el.style.borderLeftColor = 'var(--blue-mid)'
    el.style.background = 'var(--blue-light)'
  }

  var d = null
  try {
    var response = await fetch(API + '/api/discrepancies/' + id)
    if (response.ok) {
      d = await response.json()
    }
  } catch (e) {
    // Use mock data
    var mockInv = MOCK_DATA.invoices.find(function(i) { return i.id === id })
    if (mockInv) {
      var riskCategory = mockInv.risk_score >= 7 ? 'High-risk' : mockInv.risk_score >= 4 ? 'Moderate risk' : 'Low risk'
      var comparison = [
        { field: 'Vendor Name', pdf: mockInv.vendor, lhdn: mockInv.vendor + ' (Registered)', match: true },
        { field: 'SST Rate', pdf: mockInv.sst_rate, lhdn: '8% (Standard)', match: mockInv.sst_rate === '8%' },
        { field: 'Amount', pdf: 'RM ' + fmt(mockInv.amount), lhdn: 'RM ' + fmt(mockInv.amount), match: true }
      ]
      if (mockInv.flag_type) {
        comparison.push({ field: 'Flag Type', pdf: mockInv.flag_type, lhdn: 'No flag', match: false })
      }
      var reasoning = [
        { title: 'Vendor Verification', detail: 'Vendor "' + mockInv.vendor + '" verified in LHDN system.', status: 'ok' },
        { title: 'SST Rate Check', detail: 'SST rate ' + mockInv.sst_rate + ' is valid.', status: 'ok' }
      ]
      if (mockInv.flag_type) {
        reasoning.push({ title: 'Flag Detected', detail: mockInv.flag_type + ' - Manual review required.', status: 'error' })
      }
      d = {
        id: mockInv.id,
        vendor: mockInv.vendor,
        invoice_no: mockInv.invoice_no,
        amount: mockInv.amount,
        risk_score: mockInv.risk_score,
        risk_category: riskCategory,
        capital_at_risk: mockInv.agent_status === 'high_risk' ? mockInv.amount : mockInv.amount * 0.3,
        agent_status: mockInv.agent_status,
        comparison: comparison,
        reasoning_steps: reasoning
      }
    }
  }
  
  if (!d) {
    document.getElementById('disc-detail').innerHTML = '<div class="card">Not found</div>'
    return
  }
  discData[id] = d

  var stIcon = function(s) { return s === 'ok' ? '<i class="ti ti-check"></i>' : '<i class="ti ti-alert-triangle"></i>' }
  var stStyle = function(s) { return s === 'ok' ? 'background:var(--green-light);color:var(--green)' : 'background:var(--red-light);color:var(--red)' }

  var reasoningHtml = ''
  if (d.reasoning_steps && d.reasoning_steps.length > 0) {
    reasoningHtml = d.reasoning_steps.map(function(s) {
      return '<div class="reason-step">' +
        '<div class="reason-icon" style="' + stStyle(s.status) + '">' + stIcon(s.status) + '</div>' +
        '<div class="reason-text"><strong>' + s.title + '</strong><br>' + s.detail + '</div>' +
      '</div>'
    }).join('')
  }

  var comparisonHtml = ''
  if (d.comparison && d.comparison.length > 0) {
    comparisonHtml = '<div class="card">' +
      '<div class="card-header"><span class="card-title">Side-by-side comparison</span></div>' +
      '<div class="diff-grid">' +
        '<div class="diff-row">' +
          '<div class="diff-head">Field</div><div class="diff-head">Supplier PDF</div><div class="diff-head">LHDN MyInvois</div>' +
        '</div>' +
        d.comparison.map(function(c) {
          return '<div class="diff-row">' +
            '<div class="diff-cell label">' + c.field + '</div>' +
            '<div class="diff-cell ' + (c.match ? 'ok' : 'mismatch') + '">' + c.pdf + '</div>' +
            '<div class="diff-cell ok">' + c.lhdn + '</div>' +
          '</div>'
        }).join('') +
      '</div>' +
    '</div>'
  }

  document.getElementById('disc-detail').innerHTML = 
    '<div class="metric-row" style="grid-template-columns:repeat(3,1fr)">' +
      '<div class="metric-card"><div class="metric-label">Risk category</div><div class="metric-val danger" style="font-size:16px">' + (d.risk_category || '—') + '</div></div>' +
      '<div class="metric-card"><div class="metric-label">Risk score</div><div class="metric-val danger">' + (d.risk_score || 0).toFixed(1) + ' / 10</div></div>' +
      '<div class="metric-card"><div class="metric-label">Capital at risk</div><div class="metric-val danger">RM ' + fmt(d.capital_at_risk || 0) + '</div></div>' +
    '</div>' +
    '<div class="card">' +
      '<div class="card-header"><span class="card-title">Agent reasoning chain</span></div>' +
      '<div class="reason-chain">' + reasoningHtml + '</div>' +
      '<div class="approve-row">' +
        '<button class="btn danger" onclick="doAction(\'' + id + '\',\'send_comms\')"><i class="ti ti-mail"></i> Send resolution email</button>' +
        '<button class="btn" onclick="doAction(\'' + id + '\',\'hold\')"><i class="ti ti-player-pause"></i> Hold payment</button>' +
        '<button class="btn success" onclick="doAction(\'' + id + '\',\'approve\')"><i class="ti ti-check"></i> Override & approve</button>' +
      '</div>' +
    '</div>' +
    comparisonHtml
}

async function doAction(id, action) {
  try {
    await fetch(API + '/api/invoices/' + id + '/action', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: action })
    })
  } catch (e) {
    console.log('Action recorded locally (backend not available)')
  }
  alert('Action "' + action + '" recorded. Audit log updated.')
  if (action === 'send_comms') nav('comms', document.querySelector('.nav-item[onclick*="comms"]'))
}

// ── COMMS ─────────────────────────────────────────────────────────────────────

var commsSent = false

async function loadComms() {
  var fallback = { history: MOCK_DATA.comms }
  var d = await fetchWithFallback(API + '/api/comms', fallback)
  
  var historyHtml = ''
  if (d.history && d.history.length > 0) {
    historyHtml = d.history.map(function(c) {
      var statusBadge = c.sent ? rm('Sent', 'success') : rm('Draft', 'gray')
      var responseBadge = c.response === 'resolved' ? rm('Resolved · paid', 'success') : c.response === 'awaiting' ? rm('Awaiting reply', 'warning') : rm('Pending', 'gray')
      return '<tr>' +
        '<td style="font-size:12px;color:var(--muted)">' + c.date + '</td>' +
        '<td style="font-family:monospace;font-size:12px">' + c.invoice + '</td>' +
        '<td><strong>' + c.vendor + '</strong></td>' +
        '<td><span class="tag">' + c.type + '</span></td>' +
        '<td>' + statusBadge + '</td>' +
        '<td>' + responseBadge + '</td>' +
      '</tr>'
    }).join('')
  } else {
    historyHtml = '<tr><td colspan="6" style="text-align:center;color:var(--muted)">No communications found</td></tr>'
  }
  document.getElementById('comms-tbody').innerHTML = historyHtml

  var email = null
  try {
    var resp = await fetch(API + '/api/draft-email', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        vendor: 'Matahari Trading Sdn Bhd',
        invoice_no: 'MT-2026-0891',
        amount: 128000,
        issues: [
          'Entity name mismatch — PDF omits (M) suffix',
          'SST rate conflict — PDF 8% vs LHDN 0% E3 exemption'
        ]
      })
    })
    if (resp.ok) {
      email = await resp.json()
    }
  } catch (e) {
    console.log('Email draft not available (backend not running)')
  }

  var emailBody = document.getElementById('comms-email-body')
  if (email) {
    emailBody.className = 'email-preview'
    emailBody.textContent = email.body
  } else {
    emailBody.className = 'email-preview'
    emailBody.textContent = 'Dear Finance Team,\n\nRE: Invoice MT-2026-0891 - Compliance Discrepancy Notice\n\nWe have identified discrepancies in the invoice from Matahari Trading Sdn Bhd (RM 128,000.00).\n\nIssues:\n• Entity name mismatch — PDF omits (M) suffix\n• SST rate conflict — PDF 8% vs LHDN 0% E3 exemption\n\nAction Required:\n1. Please review the discrepancies and verify with the vendor\n2. Request corrected invoice if necessary\n\nBest regards,\nTaxTrace AI Audit System'
  }
}

function sendCommsEmail() {
  if (commsSent) return
  commsSent = true
  document.getElementById('comms-draft-status').className = 'badge badge-success'
  document.getElementById('comms-draft-status').textContent = '✓ Sent'
  document.getElementById('comms-send-btn').disabled = true
}

// ── ANALYTICS ─────────────────────────────────────────────────────────────────

var analyticsCharts = []

async function loadAnalytics() {
  analyticsCharts.forEach(function(c) { c.destroy() })
  analyticsCharts = []
  
  var fallback = MOCK_DATA.analytics
  var anal = await fetchWithFallback(API + '/api/analytics', fallback)
  
  document.getElementById('a-rate').textContent = (anal.compliance_rate_mtd || 0) + '%'
  document.getElementById('a-days').textContent = (anal.avg_resolution_days || 0) + ' days'
  document.getElementById('a-sst').textContent = 'RM ' + fmt(anal.sst_recovered || 0)
  document.getElementById('a-rej').textContent = anal.lhdn_rejections_avoided || 0

  var opts = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false } },
    scales: {
      x: { grid: { color: gc }, ticks: { color: tc, font: { size: 11 } } },
      y: { grid: { color: gc }, ticks: { color: tc, font: { size: 11 } } }
    }
  }

  var dashFallback = MOCK_DATA.dashboard
  var dash = await fetchWithFallback(API + '/api/dashboard', dashFallback)

  if (dash && dash.weekly_trend) {
    analyticsCharts.push(new Chart(document.getElementById('trendChart'), {
      type: 'bar',
      data: {
        labels: dash.weekly_trend.map(function(w) { return w.week }),
        datasets: [
          { label: 'Clean', data: dash.weekly_trend.map(function(w) { return w.clean }), backgroundColor: '#378ADD', stack: 's' },
          { label: 'Minor', data: dash.weekly_trend.map(function(w) { return w.minor }), backgroundColor: '#EF9F27', stack: 's' },
          { label: 'High-risk', data: dash.weekly_trend.map(function(w) { return w.high_risk }), backgroundColor: '#E24B4A', stack: 's' },
        ]
      },
      options: {
        ...opts,
        scales: {
          x: { stacked: true, ...opts.scales.x },
          y: { stacked: true, ...opts.scales.y }
        }
      }
    }))

    if (dash.discrepancy_types) {
      analyticsCharts.push(new Chart(document.getElementById('typeChart'), {
        type: 'bar',
        data: {
          labels: dash.discrepancy_types.map(function(d) { return d.type }),
          datasets: [{
            data: dash.discrepancy_types.map(function(d) { return d.count }),
            backgroundColor: ['#378ADD', '#E24B4A', '#EF9F27', '#639922', '#888'],
            borderWidth: 0
          }]
        },
        options: opts
      }))
    }

    if (dash.top_vendors_at_risk) {
      analyticsCharts.push(new Chart(document.getElementById('vendorChart'), {
        type: 'bar',
        data: {
          labels: dash.top_vendors_at_risk.map(function(v) { return v.vendor }),
          datasets: [{
            data: dash.top_vendors_at_risk.map(function(v) { return v.amount }),
            backgroundColor: dash.top_vendors_at_risk.map(function(v) { return v.level === 'high' ? '#E24B4A' : '#EF9F27' }),
            borderWidth: 0,
            borderRadius: 3
          }]
        },
        options: {
          ...opts,
          indexAxis: 'y',
          scales: {
            ...opts.scales,
            x: {
              ...opts.scales.x,
              ticks: { ...opts.scales.x.ticks, callback: function(v) { return 'RM ' + Math.round(v / 1000) + 'k' } }
            }
          }
        }
      }))
    }
  }

  if (anal && anal.monthly_trend) {
    analyticsCharts.push(new Chart(document.getElementById('monthChart'), {
      type: 'line',
      data: {
        labels: anal.monthly_trend.map(function(m) { return m.month }),
        datasets: [{
          data: anal.monthly_trend.map(function(m) { return m.rate }),
          borderColor: '#185FA5',
          backgroundColor: 'rgba(24,95,165,.08)',
          fill: true,
          tension: 0.4,
          pointBackgroundColor: '#185FA5',
          pointRadius: 4
        }]
      },
      options: {
        ...opts,
        scales: {
          x: { ...opts.scales.x },
          y: {
            ...opts.scales.y,
            min: 72,
            max: 88,
            ticks: { ...opts.scales.y.ticks, callback: function(v) { return v + '%' } }
          }
        }
      }
    }))
  }
}

// ── AUDIT LOG ─────────────────────────────────────────────────────────────────

var auditData = []

async function loadAuditLog() {
  var fallback = MOCK_DATA.audit
  var d = await fetchWithFallback(API + '/api/audit-log', fallback)
  
  auditData = d.logs || []
  document.getElementById('audit-count').textContent = (d.total || 0) + ' entries'
  
  var logHtml = ''
  if (d.logs && d.logs.length > 0) {
    logHtml = d.logs.map(function(l) {
      var resultColor = l.result === 'high_risk' ? 'danger' : l.result === 'warning' ? 'warning' : l.result === 'ok' ? 'success' : 'gray'
      return '<tr>' +
        '<td style="font-size:11.5px;color:var(--muted)">' + l.timestamp + '</td>' +
        '<td><span class="tag">' + l.agent + '</span></td>' +
        '<td style="font-family:monospace;font-size:12px">' + l.invoice + '</td>' +
        '<td>' + l.action + '</td>' +
        '<td>' + rm(l.result_label, resultColor) + '</td>' +
      '</tr>'
    }).join('')
  } else {
    logHtml = '<tr><td colspan="5" style="text-align:center;color:var(--muted)">No audit logs found</td></tr>'
  }
  document.getElementById('audit-tbody').innerHTML = logHtml
}

function exportAuditCSV() {
  var rows = [['Timestamp', 'Agent', 'Invoice', 'Action', 'Result']]
  auditData.forEach(function(l) {
    rows.push([l.timestamp, l.agent, l.invoice, l.action, l.result_label])
  })
  var csv = rows.map(function(r) {
    return r.map(function(c) { return '"' + c + '"' }).join(',')
  }).join('\n')
  var a = document.createElement('a')
  a.href = 'data:text/csv;charset=utf-8,' + encodeURIComponent(csv)
  a.download = 'taxtrace-audit-log.csv'
  a.click()
}

// ── WOW FEATURE: PDF Upload & Live Pipeline ───────────────────────────────────

var pipelineEmailData = null

function onDrag(e, enter) {
  e.preventDefault()
  document.getElementById('upload-zone').classList.toggle('drag', enter)
}

function onDrop(e) {
  e.preventDefault()
  document.getElementById('upload-zone').classList.remove('drag')
  var file = e.dataTransfer.files[0]
  if (file) startPipeline(file)
}

function onFileSelect(inp) {
  if (inp.files[0]) startPipeline(inp.files[0])
}

function setPipelineStep(n, state) {
  var circle = document.getElementById('ps-' + n)
  circle.className = 'step-circle ' + state
  if (state === 'done' && n < 6) {
    document.getElementById('pc-' + n).classList.add('done')
  }
  var progress = Math.round((n / 6) * 100)
  document.getElementById('pipeline-progress').style.width = progress + '%'
}

function showStepDetail(text) {
  var el = document.getElementById('step-detail')
  el.classList.add('show')
  el.innerHTML = text
}

async function startPipeline(file) {
  if (!file.name.toLowerCase().endsWith('.pdf')) {
    alert('Please upload a PDF file.')
    return
  }

  document.getElementById('upload-zone').style.display = 'none'
  document.getElementById('pipeline-panel').classList.add('active')
  document.getElementById('result-extracted').style.display = 'none'
  document.getElementById('result-risk').style.display = 'none'
  document.getElementById('result-email').style.display = 'none'
  pipelineEmailData = null

  for (var i = 1; i <= 6; i++) {
    document.getElementById('ps-' + i).className = 'step-circle pending'
    if (i < 6) document.getElementById('pc-' + i).classList.remove('done')
  }
  document.getElementById('pipeline-progress').style.width = '0%'
  document.getElementById('pipeline-title').textContent = 'Running AI agent pipeline — ' + file.name
  document.getElementById('pipeline-badge').innerHTML = '<span class="spin"><i class="ti ti-loader-2"></i></span> Processing'
  document.getElementById('step-detail').classList.remove('show')

  var formData = new FormData()
  formData.append('file', file)

  try {
    var resp = await fetch(API + '/api/upload-invoice', { method: 'POST', body: formData })

    if (!resp.ok) {
      simulatePipeline(file)
      return
    }

    var reader = resp.body.getReader()
    var decoder = new TextDecoder()
    var buffer = ''

    while (true) {
      var result = await reader.read()
      if (result.done) break
      buffer += decoder.decode(result.value, { stream: true })
      var lines = buffer.split('\n')
      buffer = lines.pop()

      for (var j = 0; j < lines.length; j++) {
        var line = lines[j]
        if (!line.startsWith('data: ')) continue
        var ev
        try { ev = JSON.parse(line.slice(6)) } catch (e) { continue }

        var step = ev.step
        if (step >= 1 && step <= 6) {
          if (ev.status === 'running') setPipelineStep(step, 'active')
          else if (ev.status === 'done' || ev.status === 'complete') setPipelineStep(step, 'done')
          else if (ev.status === 'error') setPipelineStep(step, 'error')

          showStepDetail('<strong>' + ev.title + '</strong><br><span style="color:var(--muted)">' + ev.detail + '</span>')

          if (ev.extracted) {
            renderExtracted(ev.extracted)
          }
          if (ev.risk) {
            renderRisk(ev.risk)
          }
          if (ev.email) {
            pipelineEmailData = ev.email
          }
          if (ev.status === 'complete') {
            document.getElementById('pipeline-title').textContent = '✓ Pipeline complete'
            document.getElementById('pipeline-badge').innerHTML = '<span style="color:var(--green)"><i class="ti ti-check"></i> Complete</span>'
            if (pipelineEmailData) renderEmail(pipelineEmailData)
          }
        }
      }
    }

  } catch (err) {
    simulatePipeline(file)
  }
}

// ── Fallback Pipeline Simulation ─────────────────────────────────────────────

function simulatePipeline(file) {
  var step = 1
  
  var steps = [
    { title: 'Ingesting PDF', detail: 'Processing file: ' + file.name },
    { title: 'AI Extraction', detail: 'Claude is analysing the invoice...' },
    { title: 'LHDN Lookup', detail: 'Validating against LHDN database...' },
    { title: 'Risk Assessment', detail: 'Calculating risk score...' },
    { title: 'Drafting Email', detail: 'AI is generating vendor communication...' },
    { title: 'Complete', detail: 'Pipeline completed successfully' }
  ]

  var vendors = ['Matahari Trading Sdn Bhd', 'Kencana Engineering', 'Sentosa Supplies', 'Bina Jaya Construction']
  var randomVendor = vendors[Math.floor(Math.random() * vendors.length)]
  var amount = Math.round((Math.random() * 150000 + 10000) / 100) * 100
  var riskScore = Math.random() * 10
  var status = riskScore > 7 ? 'high_risk' : riskScore > 4 ? 'minor_flag' : 'clean'
  var flagTypes = ['SST rate mismatch', 'Entity name mismatch', 'Registration number missing', 'Address mismatch']
  var flagType = status !== 'clean' ? flagTypes[Math.floor(Math.random() * flagTypes.length)] : null
  var extracted = null

  var interval = setInterval(function() {
    if (step > 6) {
      clearInterval(interval)
      return
    }

    var s = steps[step - 1]
    setPipelineStep(step, step < 6 ? 'done' : 'complete')
    showStepDetail('<strong>' + s.title + '</strong><br><span style="color:var(--muted)">' + s.detail + '</span>')
    
    var progress = Math.round((step / 6) * 100)
    document.getElementById('pipeline-progress').style.width = progress + '%'

    if (step === 2) {
      extracted = {
        vendor_name: randomVendor,
        invoice_no: 'INV-' + new Date().toISOString().slice(0,7).replace('-','') + '-' + Math.floor(Math.random() * 900 + 100),
        invoice_date: new Date().toISOString().slice(0,10),
        amount: amount,
        sst_rate: Math.random() > 0.5 ? '8%' : '6%',
        reg_no: 'REG-' + Math.floor(Math.random() * 900000 + 100000),
        sst_id: 'SST-' + Math.floor(Math.random() * 9000 + 1000),
        address: Math.floor(Math.random() * 900 + 100) + ' Jalan ' + ['Kuala', 'Petaling', 'Setia', 'Ampang'][Math.floor(Math.random() * 4)]
      }
      renderExtracted(extracted)
    }

    if (step === 4) {
      var categoryMap = { high_risk: 'High Risk', minor_flag: 'Minor Flag', clean: 'Clean' }
      var riskData = {
        score: riskScore,
        agent_status: status,
        category: categoryMap[status] || status,
        capital_at_risk: status === 'high_risk' ? amount : status === 'minor_flag' ? amount * 0.3 : 0,
        flag_type: flagType,
        comparison: [
          { field: 'Vendor Name', pdf: randomVendor, lhdn: randomVendor + ' (Registered)', match: true },
          { field: 'SST Rate', pdf: Math.random() > 0.5 ? '8%' : '6%', lhdn: '8% (Standard)', match: Math.random() > 0.3 },
          { field: 'Amount', pdf: 'RM ' + fmt(amount), lhdn: 'RM ' + fmt(amount), match: true }
        ],
        reasoning_steps: [
          { title: 'Vendor Verification', detail: 'Vendor "' + randomVendor + '" verified in LHDN system.', status: 'ok' },
          { title: 'Amount Validation', detail: 'Amount RM ' + fmt(amount) + ' is within acceptable range.', status: 'ok' }
        ]
      }
      if (flagType) {
        riskData.reasoning_steps.push({ title: 'Flag Detected', detail: flagType + ' - Manual review required.', status: 'error' })
        riskData.comparison.push({ field: 'Flag Type', pdf: flagType, lhdn: 'No flag', match: false })
      } else {
        riskData.reasoning_steps.push({ title: 'All Clear', detail: 'No discrepancies found. Invoice is clean.', status: 'ok' })
      }
      renderRisk(riskData)
    }

    if (step === 5 && status !== 'clean') {
      var email = {
        to: 'finance@' + randomVendor.toLowerCase().replace(/\s/g, '') + '.com.my',
        subject: 'Invoice ' + (extracted ? extracted.invoice_no : 'INV-001') + ' — LHDN Compliance Discrepancy Notice',
        body: 'Dear Finance Team,\n\nRE: Invoice ' + (extracted ? extracted.invoice_no : 'INV-001') + ' - Compliance Discrepancy Notice\n\nWe have identified discrepancies in the invoice from ' + randomVendor + ' (RM ' + fmt(amount) + ').\n\n' + (flagType ? 'Issues: • ' + flagType : 'No issues found') + '\n\nAction Required:\n1. Please review the discrepancies and verify with the vendor\n2. Request corrected invoice if necessary\n\nBest regards,\nTaxTrace AI Audit System'
      }
      pipelineEmailData = email
    }

    if (step === 6) {
      document.getElementById('pipeline-title').textContent = '✓ Pipeline complete'
      document.getElementById('pipeline-badge').innerHTML = '<span style="color:var(--green)"><i class="ti ti-check"></i> Complete</span>'
      if (pipelineEmailData) renderEmail(pipelineEmailData)
    }

    step++
  }, 800)
}

function renderExtracted(ext) {
  var keys = [
    ['vendor_name', 'Vendor name'],
    ['invoice_no', 'Invoice no.'],
    ['invoice_date', 'Date'],
    ['reg_no', 'Reg. number'],
    ['sst_id', 'SST ID'],
    ['amount', 'Amount'],
    ['sst_rate', 'SST rate'],
    ['address', 'Address']
  ]
  document.getElementById('extracted-fields').innerHTML = keys.map(function(arr) {
    var k = arr[0], l = arr[1]
    var value = ext[k] || '<span style="color:var(--muted);font-style:italic">Not found</span>'
    return '<div class="extracted-field">' +
      '<div class="ef-label">' + l + '</div>' +
      '<div class="ef-value">' + value + '</div>' +
    '</div>'
  }).join('')
  document.getElementById('result-extracted').style.display = 'block'
}

function renderRisk(risk) {
  var statusMap = { high_risk: 'danger', minor_flag: 'warning', clean: 'success' }
  var badge = document.getElementById('risk-badge')
  badge.className = 'badge badge-' + (statusMap[risk.agent_status] || 'gray')
  badge.textContent = risk.category || risk.agent_status

  var card = document.getElementById('risk-result-card')
  card.className = 'result-card ' + risk.agent_status

  var colorMap = { high_risk: 'var(--red)', minor_flag: 'var(--amber)', clean: 'var(--green)' }
  var col = colorMap[risk.agent_status] || 'var(--text)'

  document.getElementById('risk-score-display').style.color = col
  document.getElementById('risk-score-display').textContent = (risk.score || 0).toFixed(1)
  document.getElementById('risk-category-display').textContent = risk.category || risk.agent_status
  document.getElementById('risk-category-display').style.color = col
  document.getElementById('risk-capital-display').textContent = risk.capital_at_risk > 0 ? 'RM ' + fmt(risk.capital_at_risk) : '—'

  if (risk.comparison && risk.comparison.length) {
    document.getElementById('risk-diff-table').innerHTML =
      '<div class="diff-grid" style="margin-top:14px">' +
        '<div class="diff-row">' +
          '<div class="diff-head">Field</div><div class="diff-head">Supplier PDF</div><div class="diff-head">LHDN MyInvois</div>' +
        '</div>' +
        risk.comparison.map(function(c) {
          return '<div class="diff-row">' +
            '<div class="diff-cell label">' + c.field + '</div>' +
            '<div class="diff-cell ' + (c.match ? 'ok' : 'mismatch') + '">' + c.pdf + '</div>' +
            '<div class="diff-cell ok">' + c.lhdn + '</div>' +
          '</div>'
        }).join('') +
      '</div>'
  }

  document.getElementById('result-risk').style.display = 'block'

  document.getElementById('btn-send-email').onclick = function() {
    document.getElementById('result-email').scrollIntoView({ behavior: 'smooth' })
  }
  document.getElementById('btn-approve').onclick = function() {
    document.getElementById('btn-approve').textContent = '✓ Approved'
    document.getElementById('btn-approve').disabled = true
  }
  document.getElementById('btn-hold').onclick = function() {
    document.getElementById('btn-hold').textContent = '⏸ Held'
    document.getElementById('btn-hold').disabled = true
  }
}

function renderEmail(email) {
  document.getElementById('email-to').textContent = email.to
  document.getElementById('email-subject').textContent = email.subject
  document.getElementById('email-body').textContent = email.body
  document.getElementById('result-email').style.display = 'block'
  document.getElementById('btn-send-now').onclick = function() {
    document.getElementById('btn-send-now').textContent = '✓ Sent'
    document.getElementById('btn-send-now').disabled = true
  }
}

function resetUpload() {
  document.getElementById('upload-zone').style.display = 'block'
  document.getElementById('pipeline-panel').classList.remove('active')
  document.getElementById('file-input').value = ''
}

// ── Init ──────────────────────────────────────────────────────────────────────

loadDashboard()

fetch(API + '/api/health').then(function(r) { return r.json() }).then(function(d) {
  if (!d.api_key_set) document.getElementById('no-key-warn').style.display = 'block'
}).catch(function() {
  console.log('Backend not available - using fallback data')
})