(function () {
  const BUTTON_CLASS = "fcda-analyze-button";
  const PANEL_CLASS = "fcda-report-panel";
  let activeButton = null;
  let activePanel = null;
  let activeMedia = null;

  document.addEventListener("mouseover", (event) => {
    if (!(event.target instanceof Element)) {
      return;
    }

    if (event.target.closest(`.${BUTTON_CLASS}`) || event.target.closest(`.${PANEL_CLASS}`)) {
      return;
    }

    const media = findMedia(event.target);
    if (media && isAnalyzable(media)) {
      if (media === activeMedia && activeButton) {
        return;
      }
      showButton(media);
      return;
    }

    removeButton();
  });

  chrome.runtime.onMessage.addListener((message) => {
    if (message.type === "RUN_ANALYSIS_FROM_CONTEXT_MENU") {
      const media = findMediaByUrl(message.mediaUrl);
      if (media) {
        runAnalysis(media);
      }
    }
  });

  function findMedia(node) {
    if (!(node instanceof Element)) {
      return null;
    }
    return node.closest("img, video");
  }

  function isAnalyzable(media) {
    return Boolean(media.currentSrc || media.src);
  }

  function showButton(media) {
    removeButton();
    const rect = media.getBoundingClientRect();
    const button = document.createElement("button");
    button.className = BUTTON_CLASS;
    button.textContent = "Analyze Media";
    button.style.top = `${window.scrollY + rect.top + 10}px`;
    button.style.left = `${window.scrollX + rect.left + 10}px`;
    button.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      runAnalysis(media);
    });
    document.body.appendChild(button);
    activeButton = button;
    activeMedia = media;
  }

  function removeButton() {
    if (activeButton) {
      activeButton.remove();
      activeButton = null;
    }
    activeMedia = null;
  }

  function removePanel() {
    if (activePanel) {
      activePanel.remove();
      activePanel = null;
    }
  }

  function gatherContext(media) {
    return {
      media_url: media.currentSrc || media.src,
      media_type: media.tagName === "VIDEO" ? "video" : "image",
      page_url: window.location.href,
      context_text: collectNearbyText(media)
    };
  }

  function collectNearbyText(media) {
    const pieces = [];
    const parent = media.closest("article, figure, section, div");
    if (parent) {
      pieces.push((parent.innerText || "").slice(0, 500));
    }
    pieces.push(document.title || "");
    return pieces.join(" ").trim().slice(0, 800);
  }

  function findMediaByUrl(url) {
    const items = Array.from(document.querySelectorAll("img, video"));
    return items.find((item) => (item.currentSrc || item.src) === url) || null;
  }

  function runAnalysis(media) {
    removeButton();
    renderPanel({ status: "loading" });

    chrome.runtime.sendMessage(
      {
        type: "ANALYZE_MEDIA",
        payload: gatherContext(media)
      },
      (response) => {
        if (!response?.ok) {
          renderPanel({ status: "error", error: response?.error || "Analysis failed" });
          return;
        }
        renderPanel({ status: "done", result: response.result });
      }
    );
  }

  function renderPanel(state) {
    removePanel();

    const panel = document.createElement("aside");
    panel.className = PANEL_CLASS;

    if (state.status === "loading") {
      panel.innerHTML = `
        <div class="fcda-header">Fake Content Detection Assistant</div>
        <div class="fcda-status">Analyzing media...</div>
      `;
    } else if (state.status === "error") {
      panel.innerHTML = `
        <div class="fcda-shell">
          <div class="fcda-hero">
            <div>
              <div class="fcda-eyebrow">Live Detection</div>
              <div class="fcda-header">Analysis failed</div>
            </div>
          </div>
          <div class="fcda-error">${escapeHtml(state.error)}</div>
        </div>
      `;
    } else {
      const result = state.result;
      const evidenceSorted = [...result.evidence].sort((a, b) => b.score - a.score);
      const evidenceHtml = result.evidence
        .map(
          (item) => `
            <div class="fcda-evidence-item">
              <div class="fcda-evidence-head">
                <div>
                  <strong>${escapeHtml(formatLabel(item.analyzer))}</strong>
                  <div class="fcda-subtle">${escapeHtml(item.provider)} · ${escapeHtml(item.family)}</div>
                </div>
                <span>${Math.round(item.score * 100)}%</span>
              </div>
              <div class="fcda-meter"><span style="width:${Math.round(item.score * 100)}%"></span></div>
              <div class="fcda-evidence-summary">${escapeHtml(item.summary)}</div>
              <div class="fcda-detail-pills">${formatDetails(item.details)}</div>
            </div>
          `
        )
        .join("");

      const notesHtml = result.notes.map((note) => `<li>${escapeHtml(note)}</li>`).join("");
      const topSignalsHtml = evidenceSorted
        .slice(0, 3)
        .map((item) => `<span class="fcda-top-pill">${escapeHtml(formatLabel(item.analyzer))}</span>`)
        .join("");

      panel.innerHTML = `
        <div class="fcda-shell">
          <div class="fcda-hero">
            <div>
              <div class="fcda-eyebrow">Live Detection</div>
              <div class="fcda-header">Fake Content Detection Assistant</div>
              <div class="fcda-hero-copy">${escapeHtml(result.summary)}</div>
            </div>
            <div class="fcda-chip fcda-${escapeHtml(result.verdict)}">${escapeHtml(result.verdict.replaceAll("_", " "))}</div>
          </div>
          <div class="fcda-score-row">
            <div class="fcda-score-card">
              <div class="fcda-label">Authenticity</div>
              <div class="fcda-score">${Math.round(result.authenticity_score * 100)}%</div>
            </div>
            <div class="fcda-score-card">
              <div class="fcda-label">Manipulation Risk</div>
              <div class="fcda-score">${Math.round(result.suspicious_score * 100)}%</div>
            </div>
          </div>
          <div class="fcda-meta-row">
            <div><span class="fcda-label">Confidence</span><span class="fcda-inline-value">${escapeHtml(result.confidence)}</span></div>
            <div><span class="fcda-label">Pipeline</span><span class="fcda-inline-value">${escapeHtml(result.pipeline.join(", "))}</span></div>
          </div>
          <div class="fcda-section-title">Top Signals</div>
          <div class="fcda-top-signals">${topSignalsHtml}</div>
          <div class="fcda-section-title">Evidence</div>
          <div>${evidenceHtml}</div>
          <div class="fcda-section-title">Investigator Notes</div>
          <ul class="fcda-notes">${notesHtml}</ul>
        </div>
      `;
    }

    const close = document.createElement("button");
    close.className = "fcda-close-button";
    close.textContent = "Close";
    close.addEventListener("click", removePanel);
    panel.appendChild(close);

    document.body.appendChild(panel);
    activePanel = panel;
  }

  function escapeHtml(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function formatLabel(value) {
    return String(value).replaceAll("_", " ");
  }

  function formatDetails(details) {
    return Object.entries(details || {})
      .slice(0, 4)
      .map(([key, value]) => {
        const rendered = Array.isArray(value) ? value.join(", ") : String(value);
        return `<span class="fcda-detail-pill">${escapeHtml(formatLabel(key))}: ${escapeHtml(rendered.slice(0, 48))}</span>`;
      })
      .join("");
  }
})();
