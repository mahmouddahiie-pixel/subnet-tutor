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

const RAG_TIMEOUT_MS = 10000;
const LLM_TIMEOUT_MS = 120000;

async function fetchModelStatus() {
  try {
    const res = await fetch('/api/model-status');
    if (!res.ok) return null;
    return res.json();
  } catch (err) {
    console.error('[askTutor] model-status failed:', err);
    return null;
  }
}

async function callExplainApi(question, useLlm, signal) {
  const res = await fetch('/api/explain', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, use_llm: useLlm }),
    signal,
  });

  let data;
  try {
    data = await res.json();
  } catch (parseErr) {
    console.error('[askTutor] invalid JSON response:', parseErr, 'status:', res.status);
    throw new Error('invalid_json');
  }

  if (!res.ok) {
    console.error('[askTutor] HTTP error:', res.status, data);
    throw new Error(data.error || data.answer || 'request_failed');
  }

  return data;
}

async function askTutor(question, outputEl, options = {}) {
  const I18N = window.I18N || {};

  if (!question?.trim()) {
    const msg = I18N.no_response || 'No question provided';
    if (outputEl) outputEl.textContent = msg;
    console.error('[askTutor] empty question');
    return { error: 'empty_question' };
  }

  let useLlm = options.useLlm;

  if (useLlm === undefined) {
    const status = await fetchModelStatus();
    useLlm = Boolean(status?.loaded);
    if (outputEl) {
      if (status?.loading) {
        outputEl.textContent = I18N.loading_model || I18N.loading_rag || '...';
      } else if (useLlm) {
        outputEl.textContent = I18N.loading_llm || I18N.loading || 'Generating explanation...';
      } else {
        outputEl.textContent = I18N.loading_rag || I18N.loading || '...';
      }
    }
  } else if (outputEl) {
    outputEl.textContent = useLlm
      ? I18N.loading_llm || I18N.loading || 'Generating explanation...'
      : I18N.loading_rag || I18N.loading || '...';
  }

  const timeoutMs = useLlm ? LLM_TIMEOUT_MS : RAG_TIMEOUT_MS;
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const data = await callExplainApi(question, useLlm, controller.signal);
    clearTimeout(timeoutId);

    const answer = data.answer || data.error || I18N.no_response;
    if (outputEl) {
      outputEl.textContent = answer;
    }
    return data;
  } catch (err) {
    clearTimeout(timeoutId);
    console.error('[askTutor] request failed:', err);

    // If LLM timed out, fall back to fast local knowledge instead of showing an error
    if (useLlm && err.name === 'AbortError') {
      console.warn('[askTutor] LLM timed out — retrying with local knowledge');
      if (outputEl) {
        outputEl.textContent = I18N.loading_rag || 'Searching local knowledge...';
      }
      const fallbackController = new AbortController();
      const fallbackTimeout = setTimeout(() => fallbackController.abort(), RAG_TIMEOUT_MS);
      try {
        const data = await callExplainApi(question, false, fallbackController.signal);
        clearTimeout(fallbackTimeout);
        const answer =
          (I18N.llm_slow_fallback || '') +
          (data.answer || data.error || I18N.no_response);
        if (outputEl) {
          outputEl.textContent = answer;
        }
        return { ...data, mode: 'fallback', llm_timed_out: true };
      } catch (fallbackErr) {
        clearTimeout(fallbackTimeout);
        console.error('[askTutor] fallback retry failed:', fallbackErr);
        if (outputEl) {
          outputEl.textContent = I18N.request_error || I18N.no_response;
        }
        return { error: String(fallbackErr) };
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

window.askTutor = askTutor;
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
