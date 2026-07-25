const I18N = window.I18N || {};
const FINGER_TABLE = window.FINGER_TABLE || [];
let currentStep = 0;
let fingerCount = 0;
let foldCount = 0;

function fmt(template, vars) {
  return Object.entries(vars).reduce(
    (text, [key, value]) => text.replaceAll(`{${key}}`, String(value)),
    template || ''
  );
}

/** Keith Barker hand split: fingers 1–5 on left hand, 6–8 continue on right. */
function handFingerCounts(count) {
  const leftCount = count <= 0 ? 0 : Math.min(count, 5);
  const rightCount = count <= 5 ? 0 : count - 5;
  return { leftCount, rightCount };
}

function drawHands(svgEl, count) {
  if (!svgEl) return;
  const svg = svgEl;
  svg.innerHTML = '';
  const w = 500;
  const baseY = 150;
  const { leftCount, rightCount } = handFingerCounts(count);

  function drawHand(offsetX, label, raisedCount) {
    const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    g.setAttribute('transform', `translate(${offsetX}, 20)`);

    const palm = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
    palm.setAttribute('x', '40');
    palm.setAttribute('y', '80');
    palm.setAttribute('width', '80');
    palm.setAttribute('height', '60');
    palm.setAttribute('rx', '12');
    palm.setAttribute('fill', '#fcd34d');
    palm.setAttribute('stroke', '#b45309');
    g.appendChild(palm);

    for (let i = 0; i < 5; i++) {
      const finger = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
      const raised = i < raisedCount;
      finger.setAttribute('x', 45 + i * 16);
      finger.setAttribute('y', raised ? 30 : 55);
      finger.setAttribute('width', '12');
      finger.setAttribute('height', raised ? 55 : 30);
      finger.setAttribute('rx', '6');
      finger.setAttribute('fill', raised ? '#fbbf24' : '#fde68a');
      finger.setAttribute('stroke', '#b45309');
      g.appendChild(finger);
    }

    const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    text.setAttribute('x', '80');
    text.setAttribute('y', '155');
    text.setAttribute('text-anchor', 'middle');
    text.setAttribute('fill', '#475569');
    text.setAttribute('font-size', '12');
    text.textContent = label;
    g.appendChild(text);

    svg.appendChild(g);
  }

  const leftLabel =
    leftCount > 0
      ? fmt(I18N.hand_left_active || I18N.hand_left, { count: leftCount })
      : I18N.hand_left || 'Left hand';
  const rightLabel =
    rightCount > 0
      ? fmt(I18N.hand_right_active || I18N.hand_right, { count: rightCount })
      : count > 5
        ? I18N.hand_right_continue || I18N.hand_right || 'Right hand'
        : I18N.hand_right_idle || I18N.hand_right || 'Right hand';

  drawHand(30, leftLabel, leftCount);
  drawHand(270, rightLabel, rightCount);

  const powerText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
  powerText.setAttribute('x', String(w / 2));
  powerText.setAttribute('y', String(baseY));
  powerText.setAttribute('text-anchor', 'middle');
  powerText.setAttribute('fill', '#1e40af');
  powerText.setAttribute('font-size', '16');
  powerText.setAttribute('font-weight', 'bold');
  const entry = FINGER_TABLE.find((r) => r.finger === count);
  if (entry) {
    powerText.textContent = fmt(I18N.power_formula, {
      count,
      subnets: entry.subnets,
      value: entry.subnets,
    });
  } else if (count) {
    powerText.textContent = I18N.counting || '';
  } else {
    powerText.textContent = I18N.tap_raise_fingers || '';
  }
  svg.appendChild(powerText);
}

function walkthroughFeedbackText(fingerCount, data) {
  const required = window.WALKTHROUGH?.required ?? 6;
  if (data.valid) {
    return fmt(I18N.walkthrough_correct, {
      subnets: data.subnets,
      prefix: data.new_prefix,
      block_size: data.block_size,
    });
  }
  if (fingerCount <= 0) {
    return I18N.walkthrough_start || '';
  }
  const { leftCount, rightCount } = handFingerCounts(fingerCount);
  if (fingerCount <= 5) {
    return fmt(I18N.walkthrough_left_progress, {
      subnets: data.subnets,
      finger: leftCount,
      required,
    });
  }
  return fmt(I18N.walkthrough_right_progress, {
    subnets: data.subnets,
    finger: rightCount,
    required,
  });
}

function updateFingerStats(panel) {
  const entry = FINGER_TABLE.find((r) => r.finger === fingerCount);
  const subnetsEl = panel.querySelector('.stat-subnets');
  const blockEl = panel.querySelector('.stat-block');
  const prefixEl = panel.querySelector('.stat-prefix');
  if (subnetsEl) subnetsEl.textContent = entry ? entry.subnets : 0;
  if (blockEl) blockEl.textContent = entry ? entry.block_size : '—';
  if (prefixEl) prefixEl.textContent = entry ? `/ ${24 + entry.prefix_offset}` : '/24';
}

function showStep(index) {
  currentStep = index;
  document.querySelectorAll('.step-tab').forEach((tab, i) => {
    tab.classList.toggle('active', i === index);
  });
  document.querySelectorAll('.step-content').forEach((panel, i) => {
    panel.classList.toggle('active', i === index);
  });
}

document.querySelectorAll('.finger-btn').forEach((btn) => {
  btn.addEventListener('click', async () => {
    const panel = btn.closest('.step-content');
    if (btn.dataset.action === 'raise') {
      fingerCount = Math.min(8, fingerCount + 1);
    } else {
      fingerCount = 0;
    }
    const svg = panel.querySelector('.hands-svg');
    drawHands(svg, fingerCount);
    updateFingerStats(panel);

    if (panel.querySelector('#walkthrough-feedback') && window.WALKTHROUGH) {
      const res = await fetch('/api/tutorial/validate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ fingers: fingerCount, required_subnets: window.WALKTHROUGH.required }),
      });
      const data = await res.json();
      const fb = panel.querySelector('#walkthrough-feedback');
      if (fingerCount > 0) {
        fb.textContent = walkthroughFeedbackText(fingerCount, data);
        fb.style.color = data.valid ? '#166534' : '#b45309';
      } else {
        fb.textContent = '';
      }
    }
  });
});

document.getElementById('prev-step')?.addEventListener('click', () => {
  showStep(Math.max(0, currentStep - 1));
});

document.getElementById('next-step')?.addEventListener('click', () => {
  const total = document.querySelectorAll('.step-content').length;
  showStep(Math.min(total - 1, currentStep + 1));
});

document.querySelectorAll('.step-tab').forEach((tab) => {
  tab.addEventListener('click', () => showStep(Number(tab.dataset.step)));
});

document.querySelectorAll('.explain-btn').forEach((btn) => {
  btn.addEventListener('click', async () => {
    const idx = btn.dataset.step;
    const q = document.getElementById(`explain-q-${idx}`)?.value;
    const out = document.getElementById(`explain-out-${idx}`);
    if (!out) {
      console.error('[explain] output element not found for step', idx);
    }
    btn.disabled = true;
    try {
      await window.askTutor(q, out);
    } finally {
      btn.disabled = false;
    }
  });
});

const foldBtn = document.getElementById('fold-btn');
if (foldBtn) {
  foldBtn.addEventListener('click', () => {
    foldCount = Math.min(4, foldCount + 1);
    const result = document.getElementById('fold-result');
    const subnets = 2 ** foldCount;
    result.innerHTML = '';
    for (let i = 0; i < subnets; i++) {
      const div = document.createElement('div');
      div.className = 'fold-piece';
      div.textContent = fmt(I18N.fold_subnet_label, { n: i + 1 });
      result.appendChild(div);
    }
    document.getElementById('network-bar').textContent = fmt(I18N.fold_result, {
      count: foldCount,
      subnets,
    });
  });
}

document.querySelectorAll('.hands-svg').forEach((svg) => drawHands(svg, 0));

if (typeof window !== 'undefined') {
  window.handFingerCounts = handFingerCounts;
}
