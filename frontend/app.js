// ResearchMind - Ultra-Smooth Frontend Controller (Single-Line Comments Only)

(function () {
  'use strict';

  // API Configuration & Base URL
  const API_BASE = window.location.origin.includes('http') ? window.location.origin : 'http://localhost:8000';

  // Default Workspace Persistence Helper
  function getStoredDefaultWorkspace() {
    try {
      const stored = localStorage.getItem('rm_default_workspace');
      if (stored && stored.trim()) return stored.trim().toLowerCase();
      localStorage.setItem('rm_default_workspace', 'default');
      return 'default';
    } catch (e) {
      return 'default';
    }
  }

  // Workspace Persistence Helper
  function getInitialWorkspaceId() {
    try {
      const urlParams = new URLSearchParams(window.location.search);
      const fromUrl = urlParams.get('workspace') || urlParams.get('workspace_id');
      if (fromUrl && fromUrl.trim()) {
        const clean = fromUrl.trim().toLowerCase();
        localStorage.setItem('rm_workspace_id', clean);
        return clean;
      }
      const fromStorage = localStorage.getItem('rm_workspace_id');
      if (fromStorage && fromStorage.trim()) return fromStorage.trim();
      return getStoredDefaultWorkspace();
    } catch (e) {
      return 'default';
    }
  }

  // Created Workspaces Persistence Helper
  function getStoredCreatedWorkspaces() {
    try {
      const stored = localStorage.getItem('rm_created_workspaces');
      if (stored) {
        const parsed = JSON.parse(stored);
        if (Array.isArray(parsed)) {
          return parsed.map(w => String(w).trim().toLowerCase()).filter(Boolean);
        }
      }
    } catch (e) {
      // Ignore parsing errors
    }
    return [];
  }

  // Application State
  const state = {
    defaultWorkspaceId: getStoredDefaultWorkspace(),
    workspaceId: getInitialWorkspaceId(),
    createdWorkspaces: Array.from(new Set([
      'default',
      getStoredDefaultWorkspace(),
      getInitialWorkspaceId(),
      ...getStoredCreatedWorkspaces()
    ])),
    allWorkspaces: ['default'],
    sessionId: generateUUID(),
    topic: '',
    results: {},
    running: false,
    done: false,
    currentStep: null,
    revisionCount: 0,
    evalMsg: null,
    errorStep: null,
    errorMsg: null,
    isRateLimit: false,
    isLiveBackend: false,
    allSessions: [],
    activeSseSource: null,
    pendingDeleteId: null,
    pendingDeleteWorkspace: null,
    typewriterTimer: null,
  };

  // DOM Elements
  const el = {
    // Banner & Connection
    connBanner: document.getElementById('connectionBanner'),
    connBannerText: document.getElementById('connBannerText'),
    connRetryBtn: document.getElementById('connRetryBtn'),
    serverStatusIndicator: document.getElementById('serverStatusIndicator'),
    serverStatusText: document.getElementById('serverStatusText'),

    // Sidebar, Session ID & Workspace
    sidebar: document.getElementById('sidebar'),
    sidebarBackdrop: document.getElementById('sidebarBackdrop'),
    openSidebarBtn: document.getElementById('openSidebarBtn'),
    closeSidebarBtn: document.getElementById('closeSidebarBtn'),
    newResearchBtn: document.getElementById('newResearchBtn'),
    sidebarSearchInput: document.getElementById('sidebarSearchInput'),
    sidebarSessionsContainer: document.getElementById('sidebarSessionsContainer'),
    historyEmptyMsg: document.getElementById('historyEmptyMsg'),
    sidebarSessionBox: document.getElementById('sidebarSessionBox'),
    currentSessionIdDisplay: document.getElementById('currentSessionIdDisplay'),
    copySessionIdBtn: document.getElementById('copySessionIdBtn'),

    // Workspace Management & Dynamic Pills
    sidebarWorkspaceBox: document.getElementById('sidebarWorkspaceBox'),
    toggleCreateWorkspaceBtn: document.getElementById('toggleCreateWorkspaceBtn'),
    workspaceCreateInline: document.getElementById('workspaceCreateInline'),
    inlineWorkspaceInput: document.getElementById('inlineWorkspaceInput'),
    saveInlineWorkspaceBtn: document.getElementById('saveInlineWorkspaceBtn'),
    cancelInlineWorkspaceBtn: document.getElementById('cancelInlineWorkspaceBtn'),
    sidebarWorkspacePills: document.getElementById('sidebarWorkspacePills'),
    openWorkspaceModalBtn: document.getElementById('openWorkspaceModalBtn'),
    currentWorkspaceDisplay: document.getElementById('currentWorkspaceDisplay'),
    workspaceDefaultTag: document.getElementById('workspaceDefaultTag'),
    workspaceModalBackdrop: document.getElementById('workspaceModalBackdrop'),
    workspaceModalCloseBtn: document.getElementById('workspaceModalCloseBtn'),
    workspaceModalCancelBtn: document.getElementById('workspaceModalCancelBtn'),
    workspaceModalConfirmBtn: document.getElementById('workspaceModalConfirmBtn'),
    modalDefaultWorkspaceVal: document.getElementById('modalDefaultWorkspaceVal'),
    modalSetCurrentAsDefaultBtn: document.getElementById('modalSetCurrentAsDefaultBtn'),
    modalReturnToDefaultBtn: document.getElementById('modalReturnToDefaultBtn'),
    workspaceInput: document.getElementById('workspaceInput'),
    generateWorkspaceIdBtn: document.getElementById('generateWorkspaceIdBtn'),
    workspaceChipList: document.getElementById('workspaceChipList'),

    // Input & Actions
    topicInput: document.getElementById('topicInput'),
    clearTopicBtn: document.getElementById('clearTopicBtn'),
    actionBtnContainer: document.getElementById('actionBtnContainer'),
    primaryActionBtn: document.getElementById('primaryActionBtn'),
    primaryActionText: document.getElementById('primaryActionText'),

    // Feedback Banners
    evalBanner: document.getElementById('evalBanner'),
    evalBannerIcon: document.getElementById('evalBannerIcon'),
    evalBannerText: document.getElementById('evalBannerText'),
    errorBanner: document.getElementById('errorBanner'),
    errorTitle: document.getElementById('errorTitle'),
    errorDescription: document.getElementById('errorDescription'),
    errorCode: document.getElementById('errorCode'),
    errorDetailsWrap: document.getElementById('errorDetailsWrap'),

    // Unified Completion Banner
    completionBanner: document.getElementById('completionBanner'),
    completionDesc: document.getElementById('completionDesc'),
    jumpToReportBtn: document.getElementById('jumpToReportBtn'),

    // Status Cards & Live Status
    liveStatusWrap: document.getElementById('liveStatusWrap'),
    liveStatusText: document.getElementById('liveStatusText'),
    revisionIndicator: document.getElementById('revisionIndicator'),
    cards: {
      search: document.getElementById('card-search'),
      reader: document.getElementById('card-reader'),
      writer: document.getElementById('card-writer'),
      critic: document.getElementById('card-critic'),
    },
    badges: {
      search: document.getElementById('badge-search'),
      reader: document.getElementById('badge-reader'),
      writer: document.getElementById('badge-writer'),
      critic: document.getElementById('badge-critic'),
    },

    // Extracted Sources Section & User-Action Driven Expanders (Report Page)
    reportResultsSection: document.getElementById('reportResultsSection'),
    reportReaderExpanderCard: document.getElementById('reportReaderExpanderCard'),
    reportReaderExpanderHeader: document.getElementById('reportReaderExpanderHeader'),
    reportReaderChevronBtn: document.getElementById('reportReaderChevronBtn'),
    reportReaderContentBody: document.getElementById('reportReaderContentBody'),
    copyReportReaderBtn: document.getElementById('copyReportReaderBtn'),

    reportSearchExpanderCard: document.getElementById('reportSearchExpanderCard'),
    reportSearchExpanderHeader: document.getElementById('reportSearchExpanderHeader'),
    reportSearchChevronBtn: document.getElementById('reportSearchChevronBtn'),
    reportSearchContentBody: document.getElementById('reportSearchContentBody'),
    copyReportSearchBtn: document.getElementById('copyReportSearchBtn'),

    // View Containers & Report Page Elements
    processView: document.getElementById('processView'),
    reportView: document.getElementById('reportView'),
    reportTopBar: document.getElementById('reportTopBar'),
    backToProcessBtn: document.getElementById('backToProcessBtn'),
    reportNewResearchBtn: document.getElementById('reportNewResearchBtn'),
    reportTopicTitle: document.getElementById('reportTopicTitle'),
    reportMainTitle: document.getElementById('reportMainTitle'),
    reportDateBadge: document.getElementById('reportDateBadge'),
    reportScorePill: document.getElementById('reportScorePill'),
    reportScoreText: document.getElementById('reportScoreText'),

    reportContentBody: document.getElementById('reportContentBody'),
    copyReportBtn: document.getElementById('copyReportBtn'),
    downloadMdBtn: document.getElementById('downloadMdBtn'),
    downloadDocxBtn: document.getElementById('downloadDocxBtn'),
    docxBtnText: document.getElementById('docxBtnText'),
    docxSpinner: document.getElementById('docxSpinner'),

    criticBox: document.getElementById('criticBox'),
    criticScoreBadge: document.getElementById('criticScoreBadge'),
    criticContentBody: document.getElementById('criticContentBody'),

    // Modal
    deleteModalBackdrop: document.getElementById('deleteModalBackdrop'),
    modalCloseBtn: document.getElementById('modalCloseBtn'),
    modalCancelBtn: document.getElementById('modalCancelBtn'),
    modalConfirmDeleteBtn: document.getElementById('modalConfirmDeleteBtn'),

    // Workspace Delete Warning Modal
    deleteWorkspaceModalBackdrop: document.getElementById('deleteWorkspaceModalBackdrop'),
    closeDeleteWorkspaceModalBtn: document.getElementById('closeDeleteWorkspaceModalBtn'),
    cancelDeleteWorkspaceBtn: document.getElementById('cancelDeleteWorkspaceBtn'),
    confirmDeleteWorkspaceBtn: document.getElementById('confirmDeleteWorkspaceBtn'),
    workspaceDeleteModalDesc: document.getElementById('workspaceDeleteModalDesc'),

    // Toast Container
    toastContainer: document.getElementById('toastContainer'),
  };

  // Helper: UUID Generator
  function generateUUID() {
    if (crypto && crypto.randomUUID) return crypto.randomUUID();
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
      const r = (Math.random() * 16) | 0;
      const v = c === 'x' ? r : (r & 0x3) | 0x8;
      return v.toString(16);
    });
  }

  // Toast Notification System
  function showToast(message, type = 'info', duration = 3000) {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    const iconSvg = type === 'success' 
      ? '<svg class="icon icon-sm icon-success" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>'
      : type === 'danger'
      ? '<svg class="icon icon-sm icon-danger" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>'
      : '<svg class="icon icon-sm icon-accent" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>';

    toast.innerHTML = `${iconSvg}<span>${escapeHtml(message)}</span>`;
    el.toastContainer.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(10px)';
      toast.style.transition = 'all 0.3s ease';
      setTimeout(() => toast.remove(), 300);
    }, duration);
  }

  // View Switching Engine
  function switchView(targetViewName, onReady) {
    const processView = el.processView || document.getElementById('processView');
    const reportView = el.reportView || document.getElementById('reportView');
    if (!processView || !reportView) return;

    if (targetViewName === 'report') {
      if (reportView.classList.contains('active-view')) {
        if (typeof onReady === 'function') onReady();
        return;
      }

      // Smooth fade out of process view
      processView.classList.remove('active-view', 'fading-in');
      processView.classList.add('fading-out');

      setTimeout(() => {
        processView.classList.remove('fading-out');
        processView.classList.add('hidden-view');

        reportView.classList.remove('hidden-view');
        reportView.classList.add('active-view', 'fading-in');
        window.scrollTo({ top: 0, behavior: 'smooth' });

        if (typeof onReady === 'function') onReady();

        setTimeout(() => {
          reportView.classList.remove('fading-in');
        }, 450);
      }, 350);
    } else {
      if (processView.classList.contains('active-view')) {
        if (typeof onReady === 'function') onReady();
        return;
      }

      // Smooth fade out of report view
      reportView.classList.remove('active-view', 'fading-in');
      reportView.classList.add('fading-out');

      setTimeout(() => {
        reportView.classList.remove('fading-out');
        reportView.classList.add('hidden-view');

        processView.classList.remove('hidden-view');
        processView.classList.add('active-view', 'fading-in');
        window.scrollTo({ top: 0, behavior: 'smooth' });

        if (typeof onReady === 'function') onReady();

        setTimeout(() => {
          processView.classList.remove('fading-in');
        }, 450);
      }, 350);
    }
  }

  // Backend Connectivity Check
  async function checkBackendConnection() {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 2500);
      const res = await fetch(`${API_BASE}/api/sessions`, {
        signal: controller.signal,
      });
      clearTimeout(timeoutId);

      if (res.ok) {
        state.isLiveBackend = true;
        el.connBanner.classList.add('hidden');
        el.serverStatusIndicator.className = 'server-status-pill online';
        el.serverStatusText.textContent = 'Server Online';
        await loadSessions();
        return true;
      }
    } catch (e) {
      // Backend not currently reachable
    }

    state.isLiveBackend = false;
    el.connBanner.classList.remove('hidden');
    el.serverStatusIndicator.className = 'server-status-pill demo';
    el.serverStatusText.textContent = 'Demo Mode';
    loadDemoSessions();
    return false;
  }

  // Sessions Management Scoped to Active Workspace
  async function loadSessions() {
    try {
      const res = await fetch(`${API_BASE}/api/sessions?workspace_id=${encodeURIComponent(state.workspaceId)}`, {
        headers: { 'X-Workspace-Id': state.workspaceId }
      });
      if (res.ok) {
        const data = await res.json();
        state.allSessions = data.sessions || [];
        renderSessionsList(state.allSessions);
      }
    } catch (err) {
      console.warn('Failed to fetch sessions from server:', err);
    }
  }

  function loadDemoSessions() {
    const key = `researchmind_demo_sessions_${state.workspaceId}`;
    const local = localStorage.getItem(key) || (state.workspaceId === 'default' ? localStorage.getItem('researchmind_demo_sessions') : null);
    if (local) {
      try {
        state.allSessions = JSON.parse(local);
      } catch (e) {
        state.allSessions = getPrebuiltDemoSessions();
      }
    } else {
      state.allSessions = state.workspaceId === 'default' ? getPrebuiltDemoSessions() : [];
    }
    renderSessionsList(state.allSessions);
  }

  function getPrebuiltDemoSessions() {
    return [
      {
        id: 'demo-1-rag',
        topic: 'LLM Agents 2025 Architecture and Benchmarks',
        timestamp: new Date().toISOString(),
        results: {
          search: "Title: Autonomous LLM Agents: State of the Art 2025\nURL: https://arxiv.org/abs/2501.agents\nSnippet: Deep survey on agentic planning, memory consolidation, and tool usage across multimodal environments.\n\nTitle: Enterprise Agent Orchestration Systems\nURL: https://engineering.ai/agent-benchmarks\nSnippet: Quantitative benchmarking of multi-agent collaboration, verification loops, and token efficiency metrics.",
          reader: "# Core Architecture of LLM Agents (2025)\n\nAn LLM Agent represents an autonomous software system leveraging a foundation model for cognitive planning, dynamic tool invocation, and iterative error recovery.\n\n1. **Reasoning Engine**: Deconstructs high-level objectives into sequential micro-tasks.\n2. **Tool Access**: Integrates search APIs, web scrapers, and sandbox execution environments.\n3. **Self-Correction**: Employs verification critics to validate empirical claims before final synthesis.",
          writer: "# Comprehensive Research Report: LLM Agents in 2025\n\n## Executive Summary\nThe transition from single-prompt chatbots to autonomous multi-agent systems represents the defining paradigm shift of 2025 AI architecture.\n\n## Mathematical Formulation\nAgent decision dynamics and convergence are governed by:\n$$\\mathcal{R}_{total} = \\sum_{t=0}^{T} \\gamma^t \\left( r_{goal}(s_t, a_t) - \\lambda \\cdot \\tau_t \\right)$$\n\n## Key Architectural Benchmarks\n| Metric | Baseline 2024 | Multi-Agent 2025 | Gain |\n| :--- | :--- | :--- | :--- |\n| Planning Accuracy | 68.2% | 94.6% | +26.4% |\n| Hallucination Rate | 14.1% | 2.1% | -85.1% |\n| Tool Call Latency | 310ms | 45ms | 6.8x faster |\n\n## Conclusion\nMulti-agent architectures achieve unprecedented reliability through specialized task division and automated verification loops.",
          critic: "Score: 9.5 out of 10 stars\n\nStrengths:\n-> &nbsp;&nbsp;&nbsp;Rigorous mathematical formulation with clear LaTeX rendering\n-> &nbsp;&nbsp;&nbsp;Systematic empirical comparison with previous year benchmarks\n\nAreas to Improve:\n-> &nbsp;&nbsp;&nbsp;Could highlight edge deployment constraints\n\nOne line verdict:\nA high-caliber, publication-grade research brief.",
          revision_count: 0,
          eval_msg: "Great news! The report has passed our quality review and is ready for you."
        }
      }
    ];
  }

  function renderSessionsList(sessions) {
    el.sidebarSessionsContainer.innerHTML = '';
    const query = (el.sidebarSearchInput.value || '').toLowerCase().trim();

    const filtered = sessions.filter(s => {
      const topicText = (s.topic || 'Untitled Research').toLowerCase();
      return topicText.includes(query);
    });

    if (filtered.length === 0) {
      el.sidebarSessionsContainer.innerHTML = `<div class="history-empty">${query ? 'No matching research found.' : 'No history yet.'}</div>`;
      return;
    }

    const recent = filtered.slice(0, 5);
    const older = filtered.slice(5);

    recent.forEach(sess => {
      el.sidebarSessionsContainer.appendChild(createSessionElement(sess));
    });

    if (older.length > 0) {
      const toggle = document.createElement('button');
      toggle.className = 'older-sessions-toggle';
      toggle.innerHTML = `
        <span>Past Sessions (${older.length})</span>
        <svg class="icon icon-sm acc-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"></polyline></svg>
      `;

      const olderContainer = document.createElement('div');
      olderContainer.className = 'older-sessions-list hidden';

      older.forEach(sess => {
        olderContainer.appendChild(createSessionElement(sess));
      });

      toggle.addEventListener('click', () => {
        const isOpen = !olderContainer.classList.contains('hidden');
        olderContainer.classList.toggle('hidden');
        toggle.querySelector('.acc-chevron').style.transform = isOpen ? 'rotate(0deg)' : 'rotate(180deg)';
      });

      el.sidebarSessionsContainer.appendChild(toggle);
      el.sidebarSessionsContainer.appendChild(olderContainer);
    }
  }

  function createSessionElement(sess) {
    const item = document.createElement('div');
    item.className = 'session-item' + (sess.id === state.sessionId ? ' active' : '');
    item.id = `sess-item-${sess.id}`;

    const label = sess.topic ? sess.topic : 'Untitled Research';

    item.innerHTML = `
      <button class="session-btn" title="${escapeHtml(label)}">${escapeHtml(label)}</button>
      <button class="session-del-btn" title="Delete session" data-id="${sess.id}">
        <svg class="icon icon-sm" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"></path><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path></svg>
      </button>
    `;

    item.querySelector('.session-btn').addEventListener('click', () => {
      loadSessionIntoUI(sess);
    });

    item.querySelector('.session-del-btn').addEventListener('click', (e) => {
      e.stopPropagation();
      openDeleteModal(sess.id);
    });

    return item;
  }

  function loadSessionIntoUI(sess) {
    state.sessionId = sess.id;
    state.topic = sess.topic || '';
    state.results = sess.results || {};
    state.running = false;
    state.done = 'critic' in state.results;
    state.errorStep = null;
    state.errorMsg = null;
    state.revisionCount = state.results.revision_count || 0;
    state.evalMsg = state.results.eval_msg || null;

    el.topicInput.value = state.topic;
    el.clearTopicBtn.classList.toggle('hidden', !state.topic);
    el.currentSessionIdDisplay.textContent = state.sessionId;

    document.querySelectorAll('.session-item').forEach(it => it.classList.remove('active'));
    const activeItem = document.getElementById(`sess-item-${sess.id}`);
    if (activeItem) activeItem.classList.add('active');

    closeMobileSidebar();

    updateActionButtons();
    updatePipelineCards();
    updateEvaluationBanner();

    // Close report expanders by default on session load
    if (el.reportSearchExpanderCard) el.reportSearchExpanderCard.classList.remove('open');
    if (el.reportReaderExpanderCard) el.reportReaderExpanderCard.classList.remove('open');
    if (el.reportSearchExpanderHeader) el.reportSearchExpanderHeader.setAttribute('aria-expanded', 'false');
    if (el.reportReaderExpanderHeader) el.reportReaderExpanderHeader.setAttribute('aria-expanded', 'false');

    if (state.results && state.results.writer) {
      renderResults(false);
      switchView('report');
    } else {
      renderResults(false);
      switchView('process');
    }

    showToast(`Loaded "${state.topic || 'Untitled'}"`, 'info', 2000);
  }

  // Delete Modal Operations
  function openDeleteModal(sessionId) {
    state.pendingDeleteId = sessionId;
    el.deleteModalBackdrop.classList.remove('hidden');
  }

  function closeDeleteModal() {
    state.pendingDeleteId = null;
    el.deleteModalBackdrop.classList.add('hidden');
  }

  async function confirmDeleteSession() {
    const idToDelete = state.pendingDeleteId;
    if (!idToDelete) return;

    if (state.isLiveBackend) {
      try {
        const res = await fetch(`${API_BASE}/api/sessions/${encodeURIComponent(idToDelete)}?workspace_id=${encodeURIComponent(state.workspaceId)}`, {
          method: 'DELETE',
          headers: { 'X-Workspace-Id': state.workspaceId }
        });
        if (res.ok) {
          showToast('Session deleted', 'success');
        }
      } catch (e) {
        showToast('Error deleting session', 'danger');
      }
      await loadSessions();
    } else {
      state.allSessions = state.allSessions.filter(s => s.id !== idToDelete);
      const key = `researchmind_demo_sessions_${state.workspaceId}`;
      localStorage.setItem(key, JSON.stringify(state.allSessions));
      renderSessionsList(state.allSessions);
      showToast('Session deleted', 'success');
    }

    if (state.sessionId === idToDelete) {
      resetToNewResearch();
    }

    closeDeleteModal();
  }

  // Multi-Tenant Workspace Switcher Operations
  function saveCreatedWorkspaces() {
    try {
      localStorage.setItem('rm_created_workspaces', JSON.stringify(state.createdWorkspaces));
    } catch (e) {
      // Ignore localStorage error
    }
  }

  function renderWorkspacePills() {
    if (!el.sidebarWorkspacePills) return;
    el.sidebarWorkspacePills.innerHTML = '';

    // Show only the current workspace and the created workspaces
    const list = Array.from(new Set([
      state.defaultWorkspaceId,
      ...state.createdWorkspaces,
      state.workspaceId
    ])).map(w => String(w).trim().toLowerCase()).filter(Boolean);

    list.forEach(ws => {
      const isCurrent = ws === state.workspaceId;
      const isDefault = ws === state.defaultWorkspaceId;

      const pill = document.createElement('button');
      pill.type = 'button';
      pill.className = `workspace-pill ${isCurrent ? 'active' : ''}`;
      pill.setAttribute('role', 'tab');
      pill.setAttribute('aria-selected', isCurrent ? 'true' : 'false');
      pill.title = isCurrent ? `Active workspace: "${ws}"` : `Select to switch to workspace "${ws}"`;

      let inner = '';
      if (isCurrent) {
        inner += '<span class="workspace-pill-dot"></span>';
      }
      inner += `<span class="workspace-pill-name">${escapeHtml(ws)}</span>`;
      if (!isDefault) {
        inner += `<span class="workspace-pill-del" title="Delete workspace ${escapeHtml(ws)}">✕</span>`;
      }
      pill.innerHTML = inner;

      pill.addEventListener('click', (e) => {
        const delBtn = e.target.closest('.workspace-pill-del');
        if (delBtn) {
          e.stopPropagation();
          requestDeleteWorkspace(ws);
          return;
        }
        if (ws !== state.workspaceId) {
          switchWorkspace(ws);
        }
      });

      el.sidebarWorkspacePills.appendChild(pill);
    });
  }

  function updateWorkspaceUI() {
    renderWorkspacePills();
    if (el.currentWorkspaceDisplay) {
      el.currentWorkspaceDisplay.textContent = state.workspaceId;
    }
    if (el.modalDefaultWorkspaceVal) {
      el.modalDefaultWorkspaceVal.textContent = state.defaultWorkspaceId;
    }
    const isAwayFromDefault = state.workspaceId !== state.defaultWorkspaceId;
    if (el.workspaceDefaultTag) {
      el.workspaceDefaultTag.classList.toggle('hidden', isAwayFromDefault);
    }
    if (el.modalReturnToDefaultBtn) {
      el.modalReturnToDefaultBtn.classList.toggle('hidden', !isAwayFromDefault);
      el.modalReturnToDefaultBtn.textContent = `Return to Default (${state.defaultWorkspaceId})`;
    }
  }

  async function createNewWorkspace(name) {
    const clean = (name || '').trim().replace(/[^\w\-_]/g, '-').toLowerCase();
    if (!clean) {
      showToast('Please enter a valid workspace name', 'info');
      return;
    }

    // Check if workspace name is already taken locally
    const alreadyExistsLocally = state.createdWorkspaces.includes(clean) || clean === state.defaultWorkspaceId;
    if (alreadyExistsLocally) {
      showToast(`Workspace "${clean}" already exists. Please use a different workspace name.`, 'danger');
      if (el.inlineWorkspaceInput) {
        el.inlineWorkspaceInput.classList.add('input-error');
        el.inlineWorkspaceInput.focus();
        el.inlineWorkspaceInput.select();
      }
      return;
    }

    try {
      const res = await fetch(`${API_BASE}/api/workspaces`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ workspace_id: clean })
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        const errMsg = errData.detail || `Workspace "${clean}" already exists. Please use a different workspace name.`;
        showToast(errMsg, 'danger');
        if (el.inlineWorkspaceInput) {
          el.inlineWorkspaceInput.classList.add('input-error');
          el.inlineWorkspaceInput.focus();
          el.inlineWorkspaceInput.select();
        }
        return;
      }

      // Successfully registered and created on server
      state.createdWorkspaces.push(clean);
      saveCreatedWorkspaces();

      if (el.workspaceCreateInline) {
        el.workspaceCreateInline.classList.add('hidden');
      }
      if (el.inlineWorkspaceInput) {
        el.inlineWorkspaceInput.value = '';
        el.inlineWorkspaceInput.classList.remove('input-error');
      }

      switchWorkspace(clean);
      showToast(`Workspace "${clean}" created and activated`, 'success');
    } catch (e) {
      console.warn('Could not register workspace on server:', e);
      showToast('Network error while creating workspace. Please try again.', 'danger');
    }
  }

  // Workspace Deletion Warning & Confirmation Flow
  function requestDeleteWorkspace(ws) {
    if (ws === 'default' || ws === state.defaultWorkspaceId) {
      showToast('Default workspace cannot be deleted', 'info');
      return;
    }
    state.pendingDeleteWorkspace = ws;
    if (el.workspaceDeleteModalDesc) {
      el.workspaceDeleteModalDesc.innerHTML = `Are you sure you want to delete workspace <strong>"${escapeHtml(ws)}"</strong>?<br><br>All research reports, sessions, and data stored in this workspace will be permanently deleted. This action cannot be undone.`;
    }
    if (el.deleteWorkspaceModalBackdrop) {
      el.deleteWorkspaceModalBackdrop.classList.remove('hidden');
    }
  }

  function closeDeleteWorkspaceModal() {
    if (el.deleteWorkspaceModalBackdrop) {
      el.deleteWorkspaceModalBackdrop.classList.add('hidden');
    }
    state.pendingDeleteWorkspace = null;
  }

  async function confirmDeleteWorkspace() {
    const ws = state.pendingDeleteWorkspace;
    if (!ws) {
      closeDeleteWorkspaceModal();
      return;
    }
    state.createdWorkspaces = state.createdWorkspaces.filter(w => w !== ws);
    saveCreatedWorkspaces();
    try {
      await fetch(`${API_BASE}/api/workspaces/${encodeURIComponent(ws)}`, { method: 'DELETE' });
    } catch (e) {
      console.warn('Could not delete workspace on server:', e);
    }
    closeDeleteWorkspaceModal();
    if (state.workspaceId === ws) {
      switchWorkspace(state.defaultWorkspaceId);
    } else {
      updateWorkspaceUI();
    }
    showToast(`Workspace "${ws}" permanently deleted`, 'info');
  }

  async function fetchServerWorkspaces() {
    try {
      const res = await fetch(`${API_BASE}/api/workspaces`);
      if (res.ok) {
        const data = await res.json();
        const serverList = (data.workspaces || []).map(w => String(w).trim().toLowerCase()).filter(Boolean);
        state.createdWorkspaces = Array.from(new Set([
          state.defaultWorkspaceId,
          ...state.createdWorkspaces,
          ...serverList
        ]));
        saveCreatedWorkspaces();
        updateWorkspaceUI();
      }
    } catch (e) {
      console.warn('Could not fetch server workspaces:', e);
    }
  }

  function setDefaultWorkspace(targetWs) {
    const clean = (targetWs || state.workspaceId || 'default').trim().replace(/[^\w\-_]/g, '-').toLowerCase() || 'default';
    state.defaultWorkspaceId = clean;
    if (!state.createdWorkspaces.includes(clean)) {
      state.createdWorkspaces.push(clean);
      saveCreatedWorkspaces();
    }
    localStorage.setItem('rm_default_workspace', clean);
    updateWorkspaceUI();
    renderWorkspaceChips(state.createdWorkspaces);
    showToast(`"${clean}" saved as your default workspace`, 'success');
  }

  function returnToDefaultWorkspace() {
    switchWorkspace(state.defaultWorkspaceId);
  }

  async function openWorkspaceModal() {
    if (!el.workspaceModalBackdrop) return;
    if (el.workspaceInput) el.workspaceInput.value = state.workspaceId;
    updateWorkspaceUI();
    el.workspaceModalBackdrop.classList.remove('hidden');

    try {
      const res = await fetch(`${API_BASE}/api/workspaces`);
      if (res.ok) {
        const data = await res.json();
        const serverList = (data.workspaces || []).map(w => String(w).trim().toLowerCase()).filter(Boolean);
        state.createdWorkspaces = Array.from(new Set([
          state.defaultWorkspaceId,
          ...state.createdWorkspaces,
          ...serverList
        ]));
        saveCreatedWorkspaces();
        renderWorkspaceChips(state.createdWorkspaces);
      }
    } catch (e) {
      console.warn('Could not fetch workspaces:', e);
    }

    setTimeout(() => {
      if (el.workspaceInput) el.workspaceInput.focus();
    }, 50);
  }

  function closeWorkspaceModal() {
    if (el.workspaceModalBackdrop) {
      el.workspaceModalBackdrop.classList.add('hidden');
    }
  }

  function renderWorkspaceChips(workspaces) {
    if (!el.workspaceChipList) return;
    el.workspaceChipList.innerHTML = '';
    const combined = Array.from(new Set([state.defaultWorkspaceId, ...workspaces]));
    combined.forEach(ws => {
      const chip = document.createElement('button');
      chip.type = 'button';
      const isDefault = ws === state.defaultWorkspaceId;
      const isActive = ws === state.workspaceId;
      chip.className = `workspace-chip ${isActive ? 'active' : ''}`;
      chip.innerHTML = `${isDefault ? '🏠 ' : ''}${escapeHtml(ws)}`;
      chip.addEventListener('click', () => {
        if (el.workspaceInput) el.workspaceInput.value = ws;
        document.querySelectorAll('.workspace-chip').forEach(c => c.classList.remove('active'));
        chip.classList.add('active');
      });
      el.workspaceChipList.appendChild(chip);
    });
  }

  function switchWorkspace(targetWorkspaceId) {
    const clean = (targetWorkspaceId || 'default').trim().replace(/[^\w\-_]/g, '-').toLowerCase() || 'default';
    state.workspaceId = clean;
    if (!state.createdWorkspaces.includes(clean)) {
      state.createdWorkspaces.push(clean);
      saveCreatedWorkspaces();
    }
    localStorage.setItem('rm_workspace_id', clean);

    updateWorkspaceUI();
    closeWorkspaceModal();
    resetToNewResearch();
    loadSessions();
    showToast(`Switched to workspace: ${clean}`, 'success');
  }

  function generateRandomWorkspace() {
    const randomSuffix = Math.random().toString(36).substring(2, 8);
    const newWs = `ws-${randomSuffix}`;
    if (el.workspaceInput) {
      el.workspaceInput.value = newWs;
      el.workspaceInput.focus();
    }
  }

  // Reset to Fresh Session
  function resetToNewResearch() {
    if (state.activeSseSource) {
      state.activeSseSource.close();
      state.activeSseSource = null;
    }
    clearTimeout(state.typewriterTimer);

    state.sessionId = generateUUID();
    state.topic = '';
    state.results = {};
    state.running = false;
    state.done = false;
    state.currentStep = null;
    state.revisionCount = 0;
    state.evalMsg = null;
    state.errorStep = null;
    state.errorMsg = null;

    el.topicInput.value = '';
    el.clearTopicBtn.classList.add('hidden');
    el.currentSessionIdDisplay.textContent = state.sessionId;
    el.revisionIndicator.classList.add('hidden');
    if (el.completionBanner) el.completionBanner.classList.add('hidden');

    document.querySelectorAll('.session-item').forEach(it => it.classList.remove('active'));

    updateActionButtons();
    updatePipelineCards();
    updateEvaluationBanner();
    hideErrorBanner();
    el.liveStatusWrap.classList.add('hidden');
    if (el.reportSearchContentBody) el.reportSearchContentBody.innerHTML = SEARCH_EMPTY_HTML;
    if (el.reportReaderContentBody) el.reportReaderContentBody.innerHTML = READER_EMPTY_HTML;

    // Close report expanders by default on reset
    if (el.reportSearchExpanderCard) el.reportSearchExpanderCard.classList.remove('open');
    if (el.reportReaderExpanderCard) el.reportReaderExpanderCard.classList.remove('open');
    if (el.reportSearchExpanderHeader) el.reportSearchExpanderHeader.setAttribute('aria-expanded', 'false');
    if (el.reportReaderExpanderHeader) el.reportReaderExpanderHeader.setAttribute('aria-expanded', 'false');

    switchView('process');
    closeMobileSidebar();
    el.topicInput.focus();
  }

  // Action Buttons UI Rendering
  function updateActionButtons() {
    const hasResults = Object.keys(state.results).length > 0;
    const isDone = state.done;
    const isRunning = state.running;

    el.actionBtnContainer.innerHTML = '';

    if (isRunning) {
      const cancelBtn = document.createElement('button');
      cancelBtn.className = 'btn btn-secondary';
      cancelBtn.id = 'cancelBtn';
      cancelBtn.innerHTML = `
        <svg class="icon icon-danger" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="18" x="3" y="3" rx="2"></rect></svg>
        <span>Cancel Research</span>
      `;
      cancelBtn.addEventListener('click', cancelRunningResearch);
      el.actionBtnContainer.appendChild(cancelBtn);
      return;
    }

    if (hasResults && !isDone) {
      const resumeBtn = document.createElement('button');
      resumeBtn.className = 'btn btn-primary';
      resumeBtn.innerHTML = `
        <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="6 3 20 12 6 21 6 3"></polygon></svg>
        <span>Resume Research</span>
      `;
      resumeBtn.addEventListener('click', () => triggerResearch('resume'));

      const restartBtn = document.createElement('button');
      restartBtn.className = 'btn btn-secondary';
      restartBtn.innerHTML = `
        <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 0 1 15-6.7L21 8"></path><path d="M21 3v5h-5"></path><path d="M21 12a9 9 0 0 1-15 6.7L3 16"></path><path d="M3 21v-5h5"></path></svg>
        <span>Restart</span>
      `;
      restartBtn.addEventListener('click', () => triggerResearch('restart'));

      el.actionBtnContainer.appendChild(resumeBtn);
      el.actionBtnContainer.appendChild(restartBtn);
    } else if (hasResults && isDone) {
      const newBtn = document.createElement('button');
      newBtn.className = 'btn btn-primary';
      newBtn.innerHTML = `
        <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"></path></svg>
        <span>New Research</span>
      `;
      newBtn.addEventListener('click', resetToNewResearch);

      const restartBtn = document.createElement('button');
      restartBtn.className = 'btn btn-secondary';
      restartBtn.innerHTML = `
        <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 0 1 15-6.7L21 8"></path><path d="M21 3v5h-5"></path><path d="M21 12a9 9 0 0 1-15 6.7L3 16"></path><path d="M3 21v-5h5"></path></svg>
        <span>Restart</span>
      `;
      restartBtn.addEventListener('click', () => triggerResearch('restart'));

      el.actionBtnContainer.appendChild(newBtn);
      el.actionBtnContainer.appendChild(restartBtn);
    } else {
      const runBtn = document.createElement('button');
      runBtn.className = 'btn btn-primary';
      runBtn.innerHTML = `
        <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="6 3 20 12 6 21 6 3"></polygon></svg>
        <span>Run Research</span>
      `;
      runBtn.addEventListener('click', () => triggerResearch('run'));

      el.actionBtnContainer.appendChild(runBtn);
    }
  }

  // Pipeline Status & Step Cards State
  const STEPS = ['search', 'reader', 'writer', 'critic'];

  function updatePipelineCards() {
    STEPS.forEach(step => {
      const card = el.cards[step];
      const badge = el.badges[step];
      if (!card || !badge) return;

      card.className = 'step-card';
      badge.className = 'step-badge';

      if (state.errorStep === step) {
        card.classList.add('error');
        badge.classList.add('badge-error');
        badge.textContent = 'Failed';
      } else if (step in state.results) {
        card.classList.add('done');
        badge.classList.add('badge-done');
        badge.textContent = 'Done';
      } else if (state.running) {
        if (state.currentStep === step) {
          card.classList.add('active');
          badge.classList.add('badge-run');
          badge.textContent = 'Running';
        } else if (step === 'writer' && state.currentStep === 'critic') {
          card.classList.add('active');
          badge.classList.add('badge-run');
          badge.textContent = 'Reviewing';
        } else {
          let currentRunning = null;
          for (const s of STEPS) {
            if (!(s in state.results)) {
              currentRunning = s;
              break;
            }
          }
          if (currentRunning === step && !state.currentStep) {
            card.classList.add('active');
            badge.classList.add('badge-run');
            badge.textContent = 'Running';
          } else {
            badge.classList.add('badge-wait');
            badge.textContent = 'Waiting';
          }
        }
      } else {
        badge.classList.add('badge-wait');
        badge.textContent = 'Waiting';
      }
    });

    if (state.revisionCount > 0) {
      el.revisionIndicator.classList.remove('hidden');
      el.revisionIndicator.textContent = `Review ${state.revisionCount} of 3`;
    } else {
      el.revisionIndicator.classList.add('hidden');
    }
  }

  function setLiveStatus(msg, isVisible = true) {
    if (!isVisible) {
      el.liveStatusWrap.classList.add('hidden');
      return;
    }
    el.liveStatusText.textContent = msg;
    el.liveStatusWrap.classList.remove('hidden');
  }

  // Evaluation & Error Banners
  function updateEvaluationBanner() {
    if (!state.evalMsg || state.done) {
      el.evalBanner.classList.add('hidden');
      return;
    }
    el.evalBanner.classList.remove('hidden');
    el.evalBannerText.textContent = state.evalMsg;

    if (state.evalMsg.includes('passed') || state.evalMsg.includes('ready')) {
      el.evalBanner.className = 'eval-banner success';
    } else {
      el.evalBanner.className = 'eval-banner warning';
    }
  }

  function showErrorBanner(message, details = null, isRateLimit = false) {
    el.errorBanner.classList.remove('hidden');
    if (isRateLimit) {
      el.errorTitle.textContent = 'AI Service Currently at Capacity';
      el.errorDescription.textContent =
        'The model provider returned a temporary rate limit. Please wait a moment before trying again.';
      el.errorDetailsWrap.classList.add('hidden');
    } else {
      el.errorTitle.textContent = 'Encountered an Unexpected Issue';
      el.errorDescription.textContent =
        'We encountered a problem while processing your research. You can restart or modify your topic slightly.';
      if (details) {
        el.errorCode.textContent = details;
        el.errorDetailsWrap.classList.remove('hidden');
      } else {
        el.errorDetailsWrap.classList.add('hidden');
      }
    }
  }

  function hideErrorBanner() {
    el.errorBanner.classList.add('hidden');
  }

  // Trigger Research
  async function triggerResearch(mode = 'run') {
    const topic = el.topicInput.value.trim();
    if (!topic) {
      showToast('Please enter a research topic first.', 'danger');
      el.topicInput.focus();
      return;
    }

    state.topic = topic;
    hideErrorBanner();

    if (mode === 'restart') {
      state.results = {};
      state.revisionCount = 0;
      state.evalMsg = null;
      state.done = false;
    }

    state.running = true;
    state.done = false;
    state.currentStep = null;
    state.errorStep = null;
    state.errorMsg = null;

    switchView('process');

    updateActionButtons();
    updatePipelineCards();
    updateEvaluationBanner();
    renderResults(false);

    if (state.isLiveBackend) {
      startLiveSSEStream(mode);
    } else {
      startDemoSimulation(mode);
    }
  }

  // Live Server-Sent Events (SSE) Stream
  function startLiveSSEStream(mode) {
    if (state.activeSseSource) {
      state.activeSseSource.close();
    }

    const url = new URL(`${API_BASE}/api/research/stream`);
    url.searchParams.set('topic', state.topic);
    url.searchParams.set('session_id', state.sessionId);
    url.searchParams.set('mode', mode);
    url.searchParams.set('workspace_id', state.workspaceId);

    const sse = new EventSource(url.toString());
    state.activeSseSource = sse;

    setLiveStatus('Starting research workflow…');

    sse.addEventListener('init', e => {
      const data = JSON.parse(e.data);
      state.sessionId = data.session_id;
      if (data.workspace_id) {
        state.workspaceId = data.workspace_id;
        if (el.currentWorkspaceDisplay) {
          el.currentWorkspaceDisplay.textContent = state.workspaceId;
        }
      }
      el.currentSessionIdDisplay.textContent = state.sessionId;
      updatePipelineCards();
    });

    sse.addEventListener('status', e => {
      const data = JSON.parse(e.data);
      if (data.step) state.currentStep = data.step;
      setLiveStatus(data.message);
      updatePipelineCards();
    });

    sse.addEventListener('step_done', e => {
      const data = JSON.parse(e.data);
      const step = data.step;
      state.results[step] = data.data;

      if (data.eval_msg) state.evalMsg = data.eval_msg;
      if (data.score) state.results.critic_score = data.score;

      updatePipelineCards();
      updateEvaluationBanner();

      if (step === 'writer' || step === 'critic') {
        if ('writer' in state.results && 'critic' in state.results) {
          renderResults(true);
        } else {
          renderResults(false);
        }
      } else {
        renderResults(false);
      }
    });

    sse.addEventListener('revision', e => {
      const data = JSON.parse(e.data);
      state.revisionCount = data.revision_count;
      state.evalMsg = data.eval_msg;
      state.currentStep = 'writer';
      delete state.results.writer;

      updatePipelineCards();
      updateEvaluationBanner();
      renderResults(false);
      setLiveStatus(`Refining draft based on critique (Review ${state.revisionCount} of 3)...`);
    });

    sse.addEventListener('complete', e => {
      const data = JSON.parse(e.data);
      state.running = false;
      state.done = true;
      state.currentStep = null;
      state.results = data.results;
      state.evalMsg = data.eval_msg;

      sse.close();
      state.activeSseSource = null;

      setLiveStatus('', false);
      updateActionButtons();
      updatePipelineCards();
      updateEvaluationBanner();

      if (!state.typewriterTimer) {
        if (state.results.writer && !el.reportView.classList.contains('active-view')) {
          renderResults(true);
        } else {
          renderResults(false);
        }
      }

      showToast('Research report successfully generated!', 'success', 4000);
      loadSessions();
    });

    sse.addEventListener('error', e => {
      sse.close();
      state.activeSseSource = null;
      state.running = false;

      let errData = null;
      try {
        if (e.data) errData = JSON.parse(e.data);
      } catch (_) {}

      state.errorStep = (errData && errData.step) || 'critic';
      state.errorMsg = (errData && errData.error) || 'Connection interrupted';
      state.isRateLimit = (errData && errData.is_rate_limit) || false;

      setLiveStatus('', false);
      updateActionButtons();
      updatePipelineCards();
      showErrorBanner(state.errorMsg, state.errorMsg, state.isRateLimit);
      showToast('Research paused on issue', 'danger');
    });
  }

  // Fallback Demo Simulation
  function startDemoSimulation(mode) {
    setLiveStatus('Web Search is querying sources…');
    updatePipelineCards();

    setTimeout(() => {
      if (!state.running) return;
      state.results.search = `### Discovered Sources & Intelligence\n\n1. **Recent Advancements in ${state.topic}**  \n   *URL*: [https://nature.com/articles/${encodeURIComponent(state.topic.toLowerCase())}](https://nature.com)  \n   *Summary*: Peer-reviewed meta-analysis and breakthrough experimental framework.\n\n2. **Empirical Benchmarks & Metrics**  \n   *URL*: [https://science.org/findings](https://science.org)  \n   *Summary*: Quantitative field tests and reproducibility metrics across leading laboratories.`;
      updatePipelineCards();
      renderResults(false);

      setLiveStatus('Source Reader is extracting deep content…');
      setTimeout(() => {
        if (!state.running) return;
        state.results.reader = `### Deep Extracted Evidence\n\nSystematic investigation of **${state.topic}** reveals significant efficiency gains over baseline architectures. Primary data shows a 43.8% improvement in throughput alongside strict bounded error guarantees under high stress conditions.`;
        updatePipelineCards();
        renderResults(false);

        state.currentStep = 'writer';
        setLiveStatus('Report Writer is synthesizing findings…');
        updatePipelineCards();

        setTimeout(() => {
          if (!state.running) return;
          const mockReport = generateMockReport(state.topic);

          state.currentStep = 'critic';
          setLiveStatus('Quality Review is auditing report…');
          updatePipelineCards();

          setTimeout(() => {
            if (!state.running) return;
            state.results.writer = mockReport;
            state.results.critic = `Score: 9.4 out of 10 stars\n\nStrengths:\n-> &nbsp;&nbsp;&nbsp;Rigorous evidence-backed structure and verifiable sources\n-> &nbsp;&nbsp;&nbsp;Accurate LaTeX mathematical formula formulation\n\nAreas to Improve:\n-> &nbsp;&nbsp;&nbsp;Include additional long-term projections\n\nOne line verdict:\nAn impeccably crafted, publication-ready research synthesis.`;
            state.evalMsg = 'Great news! The report has passed our quality review and is ready for you.';
            state.running = false;
            state.done = true;
            state.currentStep = null;

            setLiveStatus('', false);
            updateActionButtons();
            updatePipelineCards();
            updateEvaluationBanner();
            renderResults(true);

            state.allSessions.unshift({
              id: state.sessionId,
              topic: state.topic,
              timestamp: new Date().toISOString(),
              results: state.results,
            });
            localStorage.setItem('researchmind_demo_sessions', JSON.stringify(state.allSessions));
            renderSessionsList(state.allSessions);
            showToast('Report verified and ready!', 'success', 3000);
          }, 1800);
        }, 1600);
      }, 1400);
    }, 1200);
  }

  function generateMockReport(topic) {
    return `# Comprehensive Research Report: ${topic}

## Introduction
The rapid development of **${topic}** represents a paradigm shift across contemporary scientific landscapes. This brief synthesizes real-time intelligence gathered across multi-agent workflows to outline core findings, quantitative benchmarks, and future trajectories.

## Key Findings
1. **Architectural Innovations**: Systematic redesigns deliver up to a 4.2x throughput increase while minimizing compute overhead.
2. **Empirical Benchmarks**: Field evaluations demonstrate significant variance reductions across high-stress environments.
3. **Mathematical Formulation**: State dynamics and equilibrium constants are strictly modeled by:
$$\\mathcal{E}_{system} = \\sum_{i=1}^{N} \\omega_i \\cdot \\nabla \\Phi_i(t) + \\frac{1}{2} \\kappa \\cdot \\Delta t^2$$
4. **Comparative Analysis**:
| Methodology | Precision (%) | Latency (ms) | Fault Tolerance |
| :--- | :--- | :--- | :--- |
| Baseline 2024 | 82.4% | 148ms | Moderate |
| Autonomous 2025 | 96.8% | 34ms | Resilient |

## Conclusion
Autonomous analysis confirms that **${topic}** is advancing towards scalable enterprise and academic adoption, with reproducibility metrics reaching historic highs.

## Sources
- [Nature Scientific Review](https://nature.com)
- [Science Open Intelligence Archive](https://science.org)
- [Global Research Working Group](https://arxiv.org)`;
  }

  function cancelRunningResearch() {
    if (state.activeSseSource) {
      state.activeSseSource.close();
      state.activeSseSource = null;
    }
    state.running = false;
    setLiveStatus('', false);
    updateActionButtons();
    updatePipelineCards();
    showToast('Research execution stopped', 'info');
  }

  // Safely Extract Textual Content
  function extractTextContent(val) {
    if (!val) return '';
    if (typeof val === 'string') return val;
    if (Array.isArray(val)) {
      return val
        .map(item => {
          if (typeof item === 'string') return item;
          if (item && item.text) return item.text;
          if (item && item.content) return item.content;
          return JSON.stringify(item);
        })
        .join('\n\n');
    }
    if (typeof val === 'object') {
      if (val.text) return val.text;
      if (val.content) return val.content;
      if (val.extracted_content) return val.extracted_content;
      return JSON.stringify(val, null, 2);
    }
    return String(val);
  }

  // Expander Placeholders
  const SEARCH_EMPTY_HTML = `<div class="expander-empty-state"><div class="empty-state-icon-wrap"><svg class="icon icon-accent" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg></div><span class="empty-state-title">Awaiting Search Findings</span><span class="empty-state-desc">When you run research, Web Search queries recent authoritative findings and compiles discovered URLs here.</span></div>`;

  const READER_EMPTY_HTML = `<div class="expander-empty-state"><div class="empty-state-icon-wrap"><svg class="icon icon-accent" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"></path><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"></path></svg></div><span class="empty-state-title">Awaiting Extracted Source Content</span><span class="empty-state-desc">The Source Reader will scrape the primary URL and extract deep technical content, statistics, and domain evidence here.</span></div>`;

  // Results Rendering & Expander Management
  function renderResults(enableTypewriter = false) {
    const r = state.results;

    // 1. Expander: Search Agent Findings (Report Page)
    const cleanSearchText = r && r.search ? extractTextContent(r.search) : '';
    if (el.reportSearchContentBody) {
      if (cleanSearchText) {
        renderMarkdown(cleanSearchText, el.reportSearchContentBody);
      } else {
        el.reportSearchContentBody.innerHTML = SEARCH_EMPTY_HTML;
      }
    }

    // 2. Expander: Deep Scraped & Extracted Content (Report Page)
    const cleanReaderText = r && r.reader ? extractTextContent(r.reader) : '';
    if (el.reportReaderContentBody) {
      if (cleanReaderText) {
        renderMarkdown(cleanReaderText, el.reportReaderContentBody);
      } else {
        el.reportReaderContentBody.innerHTML = READER_EMPTY_HTML;
      }
    }

    // 3. Final Report & Unified Completion Banner
    const isFinalReportReady = state.done || ('critic' in r && 'writer' in r);
    if (r.writer && isFinalReportReady) {
      if (el.completionBanner) {
        el.completionBanner.classList.remove('hidden');
        if (state.evalMsg && el.completionDesc) {
          el.completionDesc.textContent = state.evalMsg;
        }
      }

      if (el.reportTopicTitle) {
        el.reportTopicTitle.textContent = state.topic || 'Research Synthesis';
      }
      if (el.reportMainTitle) {
        el.reportMainTitle.textContent = state.topic || 'Autonomous Research Synthesis';
      }
      if (el.reportDateBadge) {
        el.reportDateBadge.textContent = new Date().toLocaleDateString(undefined, {
          year: 'numeric',
          month: 'short',
          day: 'numeric'
        });
      }

      if (el.reportScoreText) {
        const scoreMatch = (r.critic || '').match(/Score:.*?([\d\.]+)/i);
        if (scoreMatch) {
          el.reportScoreText.textContent = `${scoreMatch[1]}/10`;
        } else if (r.critic_score) {
          el.reportScoreText.textContent = `${r.critic_score}/10`;
        } else {
          el.reportScoreText.textContent = 'Verified';
        }
      }

      if (r.critic && el.criticBox) {
        el.criticBox.classList.remove('hidden');
        renderCriticContent(r.critic);
      }

      if (enableTypewriter) {
        switchView('report', () => {
          streamTypewriter(r.writer, el.reportContentBody);
        });
      } else {
        clearTimeout(state.typewriterTimer);
        state.typewriterTimer = null;
        renderMarkdown(r.writer, el.reportContentBody);
      }
    } else {
      if (el.completionBanner) el.completionBanner.classList.add('hidden');
      if (el.criticBox) el.criticBox.classList.add('hidden');
    }
  }

  // Smooth Text Streaming Engine
  function streamTypewriter(fullText, targetElement) {
    clearTimeout(state.typewriterTimer);
    targetElement.innerHTML = '';

    const blocks = fullText.split(/\n\n+/);
    let blockIndex = 0;
    let charIndex = 0;

    const completedContainer = document.createElement('div');
    completedContainer.className = 'stream-completed-wrap';
    targetElement.appendChild(completedContainer);

    const activeBlock = document.createElement('div');
    activeBlock.className = 'stream-active-block';
    targetElement.appendChild(activeBlock);

    function step() {
      if (blockIndex < blocks.length) {
        const currentBlock = blocks[blockIndex];

        if (currentBlock.trim().startsWith('$$') || currentBlock.trim().startsWith('|')) {
          const atomEl = document.createElement('div');
          renderMarkdown(currentBlock, atomEl);
          completedContainer.appendChild(atomEl);
          activeBlock.innerHTML = '';
          blockIndex++;
          charIndex = 0;
          state.typewriterTimer = setTimeout(step, 140);
          return;
        }

        const stepSize = Math.min(3, currentBlock.length - charIndex);
        charIndex += stepSize;

        const slice = currentBlock.substring(0, charIndex);
        activeBlock.innerHTML = `<p>${escapeHtml(slice)}<span class="stream-cursor"></span></p>`;

        if (charIndex >= currentBlock.length) {
          const renderedEl = document.createElement('div');
          renderMarkdown(currentBlock, renderedEl);
          completedContainer.appendChild(renderedEl);
          activeBlock.innerHTML = '';

          blockIndex++;
          charIndex = 0;
          state.typewriterTimer = setTimeout(step, 130);
        } else {
          state.typewriterTimer = setTimeout(step, 30);
        }
      } else {
        activeBlock.remove();
        renderMarkdown(fullText, targetElement);
        state.typewriterTimer = null;
      }
    }

    step();
  }

  // Markdown & KaTeX Formula Renderer
  function renderMarkdown(rawMd, container) {
    if (!rawMd) {
      container.innerHTML = '';
      return;
    }

    if (window.marked && window.DOMPurify) {
      let processedMd = rawMd
        .replace(/\\\[\s*([\s\S]*?)\s*\\\]/g, '\n\n$$\n$1\n$$\n\n')
        .replace(/\\\(\s*([\s\S]*?)\s*\\\)/g, '$$$1$$')
        .replace(/(?:^|\n)\[\s*(\\[a-zA-Z0-9_\^\{\}\+\-\*/=\(\)\s\\,]+?)\s*\](?:\n|$)/g, '\n\n$$\n$1\n$$\n\n');

      const mathTokens = [];

      processedMd = processedMd.replace(/\$\$([\s\S]*?)\$\$/g, (match, formula) => {
        const token = `@@KATEX_DISPLAY_${mathTokens.length}@@`;
        mathTokens.push({ type: 'display', formula: formula.trim(), token });
        return token;
      });

      processedMd = processedMd.replace(/\$([^\$\n]+?)\$/g, (match, formula) => {
        const token = `@@KATEX_INLINE_${mathTokens.length}@@`;
        mathTokens.push({ type: 'inline', formula: formula.trim(), token });
        return token;
      });

      marked.setOptions({
        gfm: true,
        breaks: true,
      });

      let dirtyHtml = marked.parse(processedMd);

      if (window.katex) {
        mathTokens.forEach(({ type, formula, token }) => {
          try {
            const renderedMath = window.katex.renderToString(formula, {
              displayMode: type === 'display',
              throwOnError: false,
              output: 'html',
            });
            dirtyHtml = dirtyHtml.split(token).join(renderedMath);
          } catch (err) {
            dirtyHtml = dirtyHtml.split(token).join(`<span class="katex-error">${formula}</span>`);
          }
        });
      } else {
        mathTokens.forEach(({ type, formula, token }) => {
          const wrap = type === 'display' ? `$$${formula}$$` : `$${formula}$`;
          dirtyHtml = dirtyHtml.split(token).join(wrap);
        });
      }

      const cleanHtml = DOMPurify.sanitize(dirtyHtml, {
        ADD_TAGS: ['span', 'math', 'annotation', 'semantics', 'mrow', 'mi', 'mo', 'msub', 'msup', 'msubsup', 'mfrac'],
        ADD_ATTR: ['target', 'rel', 'class', 'style', 'aria-hidden'],
      });
      container.innerHTML = cleanHtml;

      container.querySelectorAll('a').forEach(a => {
        a.setAttribute('target', '_blank');
        a.setAttribute('rel', 'noopener noreferrer');
      });
    } else {
      container.textContent = rawMd;
    }
  }

  // Critic Content Presentation
  function renderCriticContent(criticText) {
    renderMarkdown(criticText, el.criticContentBody);

    const scoreMatch = criticText.match(/Score:.*?([\d\.]+)/i);
    let scoreNum = 10;
    if (scoreMatch) {
      const parsed = parseFloat(scoreMatch[1]);
      if (!isNaN(parsed)) scoreNum = parsed;
    }

    const starCount = Math.round((scoreNum / 10) * 5);
    const stars = '★'.repeat(starCount) + '☆'.repeat(5 - starCount);

    el.criticScoreBadge.innerHTML = `<span class="score-val">Score: ${scoreNum}/10</span> <span class="score-stars">(${stars})</span>`;
  }

  // Export Operations
  function downloadMarkdownFile() {
    if (!state.results.writer) {
      showToast('No report to download', 'danger');
      return;
    }

    const blob = new Blob([state.results.writer], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    const safeTopic = (state.topic || 'Research_Report').replace(/[^\w\-_]/g, '_');
    a.href = url;
    a.download = `Research_Report_${safeTopic}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    showToast('Markdown report downloaded', 'success');
  }

  async function downloadDocxFile() {
    if (!state.results.writer) {
      showToast('No report to export', 'danger');
      return;
    }

    el.docxBtnText.textContent = 'Generating...';
    el.docxSpinner.classList.remove('hidden');
    el.downloadDocxBtn.disabled = true;

    if (state.isLiveBackend) {
      try {
        const res = await fetch(`${API_BASE}/api/export/docx`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            markdown: state.results.writer,
            topic: state.topic,
          }),
        });

        if (res.ok) {
          const blob = await res.blob();
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          const safeTopic = (state.topic || 'Research_Report').replace(/[^\w\-_]/g, '_');
          a.href = url;
          a.download = `Research_Report_${safeTopic}.docx`;
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          URL.revokeObjectURL(url);
          showToast('Document downloaded', 'success');
        } else {
          throw new Error('Server export error');
        }
      } catch (e) {
        showToast('DOCX export failed, downloading Markdown instead', 'danger');
        downloadMarkdownFile();
      }
    } else {
      setTimeout(() => {
        downloadMarkdownFile();
        showToast('Demo: Document downloaded as Markdown', 'info');
      }, 700);
    }

    el.docxBtnText.textContent = '.DOCX';
    el.docxSpinner.classList.add('hidden');
    el.downloadDocxBtn.disabled = false;
  }

  // Copy Utilities
  async function copyToClipboard(text, successMsg) {
    try {
      await navigator.clipboard.writeText(text);
      showToast(successMsg, 'success');
    } catch (e) {
      showToast('Failed to copy to clipboard', 'danger');
    }
  }

  function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/[&<>"']/g, function (m) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[m];
    });
  }

  // User-Action Driven Expander Setup
  function setupExpander(cardEl, headerEl, chevronBtn) {
    if (!cardEl || !headerEl) return;

    function toggle() {
      const isOpen = cardEl.classList.contains('open');
      cardEl.classList.toggle('open', !isOpen);
      headerEl.setAttribute('aria-expanded', !isOpen);
    }

    headerEl.addEventListener('click', (e) => {
      if (e.target.closest('.copy-btn')) return;
      toggle();
    });

    headerEl.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        if (e.target.closest('.copy-btn')) return;
        e.preventDefault();
        toggle();
      }
    });

    if (chevronBtn) {
      chevronBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        toggle();
      });
    }
  }

  // Mobile Drawer Controls
  function openMobileSidebar() {
    el.sidebar.classList.add('open');
    el.sidebarBackdrop.classList.add('open');
  }

  function closeMobileSidebar() {
    el.sidebar.classList.remove('open');
    el.sidebarBackdrop.classList.remove('open');
  }

  // Event Listeners Setup
  function setupEventListeners() {
    el.topicInput.addEventListener('input', () => {
      state.topic = el.topicInput.value;
      el.clearTopicBtn.classList.toggle('hidden', !el.topicInput.value);
    });

    el.clearTopicBtn.addEventListener('click', () => {
      el.topicInput.value = '';
      state.topic = '';
      el.clearTopicBtn.classList.add('hidden');
      el.topicInput.focus();
    });

    el.topicInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        triggerResearch('run');
      }
    });

    // Session ID Copy Handler
    if (el.copySessionIdBtn) {
      el.copySessionIdBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        copyToClipboard(state.sessionId, 'Session ID copied to clipboard');
      });
    }
    if (el.sidebarSessionBox) {
      el.sidebarSessionBox.addEventListener('click', () => {
        copyToClipboard(state.sessionId, 'Session ID copied to clipboard');
      });
    }

    el.sidebarSearchInput.addEventListener('input', () => {
      renderSessionsList(state.allSessions);
    });

    el.newResearchBtn.addEventListener('click', resetToNewResearch);

    // Setup Report Expanders
    if (el.reportSearchExpanderCard && el.reportSearchExpanderHeader) {
      setupExpander(el.reportSearchExpanderCard, el.reportSearchExpanderHeader, el.reportSearchChevronBtn);
    }
    if (el.reportReaderExpanderCard && el.reportReaderExpanderHeader) {
      setupExpander(el.reportReaderExpanderCard, el.reportReaderExpanderHeader, el.reportReaderChevronBtn);
    }

    // Report Expander Copy Buttons
    if (el.copyReportSearchBtn) {
      el.copyReportSearchBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        copyToClipboard(extractTextContent(state.results.search || ''), 'Search findings copied');
      });
    }
    if (el.copyReportReaderBtn) {
      el.copyReportReaderBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        copyToClipboard(extractTextContent(state.results.reader || ''), 'Extracted source content copied');
      });
    }

    // Report Actions
    if (el.copyReportBtn) {
      el.copyReportBtn.addEventListener('click', () => {
        copyToClipboard(state.results.writer || '', 'Report copied to clipboard');
      });
    }
    if (el.downloadMdBtn) el.downloadMdBtn.addEventListener('click', downloadMarkdownFile);
    if (el.downloadDocxBtn) el.downloadDocxBtn.addEventListener('click', downloadDocxFile);

    // Dedicated Report Navigation
    if (el.backToProcessBtn) {
      el.backToProcessBtn.addEventListener('click', () => switchView('process'));
    }
    if (el.reportNewResearchBtn) {
      el.reportNewResearchBtn.addEventListener('click', resetToNewResearch);
    }
    if (el.jumpToReportBtn) {
      el.jumpToReportBtn.addEventListener('click', () => switchView('report'));
    }

    // Scroll Behavior: Hide top bar when scrolling down, reveal at top or mouse hover
    let lastScrollY = window.scrollY;
    window.addEventListener('scroll', () => {
      const topBar = el.reportTopBar || document.getElementById('reportTopBar');
      if (!topBar) return;
      const currentScrollY = window.scrollY;

      if (currentScrollY <= 25) {
        topBar.classList.remove('bar-hidden');
        lastScrollY = currentScrollY;
        return;
      }

      if (currentScrollY < lastScrollY && currentScrollY > 30) {
        topBar.classList.add('bar-hidden');
      } else if (currentScrollY > lastScrollY && currentScrollY > 60) {
        topBar.classList.add('bar-hidden');
      }

      lastScrollY = currentScrollY;
    }, { passive: true });

    window.addEventListener('mousemove', (e) => {
      const topBar = el.reportTopBar || document.getElementById('reportTopBar');
      if (!topBar) return;
      if (e.clientY <= 55) {
        topBar.classList.remove('bar-hidden');
      }
    });

    // Workspace Pill Switcher & Inline Creation Events
    if (el.toggleCreateWorkspaceBtn) {
      el.toggleCreateWorkspaceBtn.addEventListener('click', () => {
        if (el.workspaceCreateInline) {
          const isHidden = el.workspaceCreateInline.classList.toggle('hidden');
          if (!isHidden && el.inlineWorkspaceInput) {
            el.inlineWorkspaceInput.value = '';
            el.inlineWorkspaceInput.focus();
          }
        }
      });
    }
    if (el.saveInlineWorkspaceBtn) {
      el.saveInlineWorkspaceBtn.addEventListener('click', () => {
        if (el.inlineWorkspaceInput) {
          createNewWorkspace(el.inlineWorkspaceInput.value);
        }
      });
    }
    if (el.cancelInlineWorkspaceBtn) {
      el.cancelInlineWorkspaceBtn.addEventListener('click', () => {
        if (el.workspaceCreateInline) el.workspaceCreateInline.classList.add('hidden');
      });
    }
    if (el.inlineWorkspaceInput) {
      el.inlineWorkspaceInput.addEventListener('input', () => {
        el.inlineWorkspaceInput.classList.remove('input-error');
      });
      el.inlineWorkspaceInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          createNewWorkspace(el.inlineWorkspaceInput.value);
        } else if (e.key === 'Escape') {
          if (el.workspaceCreateInline) el.workspaceCreateInline.classList.add('hidden');
        }
      });
    }
    if (el.openWorkspaceModalBtn) el.openWorkspaceModalBtn.addEventListener('click', openWorkspaceModal);
    if (el.workspaceModalCloseBtn) el.workspaceModalCloseBtn.addEventListener('click', closeWorkspaceModal);
    if (el.workspaceModalCancelBtn) el.workspaceModalCancelBtn.addEventListener('click', closeWorkspaceModal);
    if (el.modalReturnToDefaultBtn) el.modalReturnToDefaultBtn.addEventListener('click', returnToDefaultWorkspace);
    if (el.modalSetCurrentAsDefaultBtn) {
      el.modalSetCurrentAsDefaultBtn.addEventListener('click', () => setDefaultWorkspace(state.workspaceId));
    }
    if (el.workspaceModalBackdrop) {
      el.workspaceModalBackdrop.addEventListener('click', (e) => {
        if (e.target === el.workspaceModalBackdrop) closeWorkspaceModal();
      });
    }
    if (el.workspaceModalConfirmBtn) {
      el.workspaceModalConfirmBtn.addEventListener('click', () => {
        const val = el.workspaceInput ? el.workspaceInput.value : '';
        createNewWorkspace(val);
      });
    }
    if (el.workspaceInput) {
      el.workspaceInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          createNewWorkspace(el.workspaceInput.value);
        }
      });
    }
    if (el.generateWorkspaceIdBtn) {
      el.generateWorkspaceIdBtn.addEventListener('click', generateRandomWorkspace);
    }

    // Modal Events
    el.modalCloseBtn.addEventListener('click', closeDeleteModal);
    el.modalCancelBtn.addEventListener('click', closeDeleteModal);
    el.modalConfirmDeleteBtn.addEventListener('click', confirmDeleteSession);
    el.deleteModalBackdrop.addEventListener('click', (e) => {
      if (e.target === el.deleteModalBackdrop) closeDeleteModal();
    });

    // Workspace Delete Warning Modal Events
    if (el.closeDeleteWorkspaceModalBtn) {
      el.closeDeleteWorkspaceModalBtn.addEventListener('click', closeDeleteWorkspaceModal);
    }
    if (el.cancelDeleteWorkspaceBtn) {
      el.cancelDeleteWorkspaceBtn.addEventListener('click', closeDeleteWorkspaceModal);
    }
    if (el.confirmDeleteWorkspaceBtn) {
      el.confirmDeleteWorkspaceBtn.addEventListener('click', confirmDeleteWorkspace);
    }
    if (el.deleteWorkspaceModalBackdrop) {
      el.deleteWorkspaceModalBackdrop.addEventListener('click', (e) => {
        if (e.target === el.deleteWorkspaceModalBackdrop) closeDeleteWorkspaceModal();
      });
    }

    // Mobile Sidebar
    if (el.openSidebarBtn) el.openSidebarBtn.addEventListener('click', openMobileSidebar);
    if (el.closeSidebarBtn) el.closeSidebarBtn.addEventListener('click', closeMobileSidebar);
    if (el.sidebarBackdrop) el.sidebarBackdrop.addEventListener('click', closeMobileSidebar);

    // Connection retry
    el.connRetryBtn.addEventListener('click', async () => {
      el.connRetryBtn.querySelector('span') ? el.connRetryBtn.querySelector('span').textContent = 'Checking…' : null;
      await checkBackendConnection();
      el.connRetryBtn.querySelector('span') ? el.connRetryBtn.querySelector('span').textContent = 'Retry' : null;
    });

    // Global keyboard shortcuts
    window.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        closeDeleteModal();
        closeDeleteWorkspaceModal();
        closeWorkspaceModal();
        closeMobileSidebar();
      }
    });
  }

  // App Initialization
  async function init() {
    updateWorkspaceUI();
    el.currentSessionIdDisplay.textContent = state.sessionId;
    setupEventListeners();
    updateActionButtons();
    updatePipelineCards();

    await checkBackendConnection();
    await fetchServerWorkspaces();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
