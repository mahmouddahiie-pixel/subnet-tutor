async function setLanguage(lang) {
  await fetch('/api/language', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ lang }),
  });
  window.location.reload();
}

document.querySelectorAll('.lang-switch button').forEach((btn) => {
  btn.addEventListener('click', () => setLanguage(btn.dataset.lang));
});

const RAG_TIMEOUT_MS = 15000;
const LLM_TIMEOUT_MS = 180000;
const MODEL_POLL_MS = 2000;
const MODEL_POLL_MAX = 45;

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function fetchModelStatus() {
  try {
    const res = await fetch('/api/model-status');
    if (!res.ok) return null;
    return res.json();
  } catch (err) {
    console.error('[tutor] model-status failed:', err);
    return null;
  }
}

async function callTutorApi(url, body, useLlm, signal) {
  const payload = { ...body, use_llm: useLlm };
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    signal,
  });

  let data;
  try {
    data = await res.json();
  } catch (parseErr) {
    console.error('[tutor] invalid JSON:', parseErr, 'status:', res.status);
    throw new Error('invalid_json');
  }

  if (!res.ok) {
    throw new Error(data.error || data.answer || 'request_failed');
  }
  return data;
}

async function requestWithTimeout(url, body, useLlm, timeoutMs) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await callTutorApi(url, body, useLlm, controller.signal);
  } finally {
    clearTimeout(timeoutId);
  }
}

async function waitForModelLoaded() {
  for (let i = 0; i < MODEL_POLL_MAX; i++) {
    const status = await fetchModelStatus();
    if (status?.loaded) return status;
    if (status?.status === 'error') return status;
    await sleep(MODEL_POLL_MS);
  }
  return fetchModelStatus();
}

async function tutorRequest(url, body, outputEl, options = {}) {
  const I18N = window.I18N || {};
  let useLlm = options.useLlm;

  const status = await fetchModelStatus();
  if (useLlm === undefined) {
    useLlm = Boolean(status?.loaded);
  }

  if (outputEl) {
    if (status?.loading && !status?.loaded) {
      outputEl.textContent = I18N.loading_model || I18N.loading_rag || '...';
    } else if (useLlm) {
      outputEl.textContent = I18N.loading_llm || 'Generating explanation...';
    } else {
      outputEl.textContent = I18N.loading_rag || 'Searching local knowledge...';
    }
  }

  const tryRequest = async (llm) => {
    const timeoutMs = llm ? LLM_TIMEOUT_MS : RAG_TIMEOUT_MS;
    return requestWithTimeout(url, body, llm, timeoutMs);
  };

  try {
    let data = await tryRequest(useLlm);

    // Model still loading — wait and retry once with LLM when ready
    if (
      !useLlm &&
      data.mode === 'fallback' &&
      (data.model_status === 'loading' || data.model_status === 'pending')
    ) {
      if (outputEl) {
        outputEl.textContent = I18N.loading_model || 'Waiting for model...';
      }
      const ready = await waitForModelLoaded();
      updateFooterStatus(ready);
      if (ready?.loaded) {
        if (outputEl) {
          outputEl.textContent = I18N.loading_llm || 'Generating explanation...';
        }
        data = await tryRequest(true);
      }
    }

    const answer = data.answer || data.error || I18N.no_response;
    if (outputEl) outputEl.textContent = answer;
    return data;
  } catch (err) {
    console.error('[tutor] request failed:', err);

    if (useLlm && err.name === 'AbortError') {
      if (outputEl) outputEl.textContent = I18N.loading_rag || 'Searching local knowledge...';
      try {
        const data = await tryRequest(false);
        const answer =
          (I18N.llm_slow_fallback || '') + (data.answer || I18N.no_response);
        if (outputEl) outputEl.textContent = answer;
        return { ...data, mode: 'fallback', llm_timed_out: true };
      } catch (fallbackErr) {
        console.error('[tutor] fallback failed:', fallbackErr);
      }
    }

    if (outputEl) {
      outputEl.textContent =
        err.name === 'AbortError'
          ? I18N.request_timeout || I18N.no_response
          : I18N.request_error || I18N.no_response;
    }
    return { error: err.message || String(err) };
  }
}

async function askTutor(question, outputEl, options = {}) {
  if (!question?.trim()) {
    const msg = (window.I18N || {}).no_response || 'No question provided';
    if (outputEl) outputEl.textContent = msg;
    return { error: 'empty_question' };
  }
  return tutorRequest('/api/explain', { question }, outputEl, options);
}

async function askHint(scenario, outputEl) {
  return tutorRequest('/api/game/hint', { scenario }, outputEl);
}

window.askTutor = askTutor;
window.askHint = askHint;
window.fetchModelStatus = fetchModelStatus;

function updateFooterStatus(status) {
  const el = document.getElementById('footer-status');
  const I18N = window.I18N || {};
  if (!el || !status) return;

  const offline = I18N.offline_note || 'Runs 100% offline after setup';
  let suffix = I18N.footer_tutor_fallback || 'Tutor fallback mode';

  if (status.loaded) {
    suffix = I18N.footer_llm_ready || 'LLM ready';
  } else if (status.loading) {
    suffix = I18N.loading_model || 'Loading model...';
  } else if (status.error || status.status === 'error') {
    suffix = I18N.footer_model_error || 'LLM load failed';
  } else if (!status.available) {
    suffix = I18N.footer_tutor_fallback || 'Tutor fallback mode';
  }

  el.textContent = `${offline} · ${suffix}`;
}

async function pollModelStatus() {
  const status = await fetchModelStatus();
  if (!status) return;
  updateFooterStatus(status);
  if (!status.loaded && (status.loading || status.status === 'pending')) {
    setTimeout(pollModelStatus, 3000);
  }
}

if (document.getElementById('footer-status')) {
  pollModelStatus();
}
