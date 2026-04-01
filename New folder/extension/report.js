chrome.runtime.sendMessage({ type: "GET_LATEST_REPORT" }, (response) => {
  const root = document.getElementById("app");
  if (!root) {
    return;
  }

  const result = response?.result;
  const meta = response?.meta;
  if (!result) {
    root.textContent = "No analysis has been run yet.";
    return;
  }

  const evidenceHtml = result.evidence
    .map(
      (item) => `
        <div class="card">
          <strong>${escapeHtml(formatLabel(item.analyzer))}</strong>
          <div class="muted">${escapeHtml(item.provider)} · ${escapeHtml(item.family)} · ${Math.round(item.score * 100)}% risk</div>
          <div>${escapeHtml(item.summary)}</div>
        </div>
      `
    )
    .join("");

  const pipelineHtml = result.pipeline.map((item) => `<span class="pill">${escapeHtml(item)}</span>`).join("");
  const notesHtml = result.notes.map((note) => `<li>${escapeHtml(note)}</li>`).join("");

  root.innerHTML = `
    <div class="card hero">
      <div><strong>Verdict:</strong> ${escapeHtml(result.verdict.replaceAll("_", " "))}</div>
      <div class="score">${Math.round(result.authenticity_score * 100)}%</div>
      <div>${escapeHtml(result.summary)}</div>
    </div>
    <div class="card">
      <div><strong>Manipulation risk:</strong> ${Math.round(result.suspicious_score * 100)}%</div>
      <div><strong>Confidence:</strong> ${escapeHtml(result.confidence)}</div>
      <div><strong>Media type:</strong> ${escapeHtml(result.media_type)}</div>
      <div><strong>Page:</strong> ${escapeHtml(meta?.pageUrl || "Unknown")}</div>
      <div><strong>Pipeline:</strong></div>
      <div>${pipelineHtml}</div>
    </div>
    ${evidenceHtml}
    <div class="card">
      <strong>Notes</strong>
      <ul>${notesHtml}</ul>
    </div>
  `;
});

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
