const API_BASE = "http://127.0.0.1:8000";

chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "analyze-media",
    title: "Analyze Media",
    contexts: ["image", "video"]
  });
});

chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId !== "analyze-media" || !tab?.id) {
    return;
  }

  chrome.tabs.sendMessage(tab.id, {
    type: "RUN_ANALYSIS_FROM_CONTEXT_MENU",
    mediaUrl: info.srcUrl
  });
});

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === "ANALYZE_MEDIA") {
    analyzeMedia(message.payload)
      .then((result) => {
        chrome.storage.local.set({
          latestReport: result,
          latestRequestMeta: {
            mediaUrl: message.payload.media_url,
            mediaType: message.payload.media_type,
            pageUrl: message.payload.page_url
          }
        });
        sendResponse({ ok: true, result });
      })
      .catch((error) => {
        sendResponse({ ok: false, error: error.message || "Unknown error" });
      });
    return true;
  }

  if (message.type === "GET_LATEST_REPORT") {
    chrome.storage.local.get(["latestReport", "latestRequestMeta"], (data) => {
      sendResponse({
        ok: true,
        result: data.latestReport || null,
        meta: data.latestRequestMeta || null
      });
    });
    return true;
  }

  return false;
});

async function analyzeMedia(payload) {
  const response = await fetch(`${API_BASE}/analyze/url`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    throw new Error(await safeError(response));
  }

  return response.json();
}

async function safeError(response) {
  try {
    const body = await response.json();
    return body.detail || `Request failed with status ${response.status}`;
  } catch {
    return `Request failed with status ${response.status}`;
  }
}
