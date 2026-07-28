const I18N = window.I18N || {};
const scenario = JSON.parse(document.getElementById('scenario-data')?.textContent || '{}');
const feedbackEl = document.getElementById('game-feedback');
const hintEl = document.getElementById('hint-output');

function collectAnswer() {
  const answer = {};
  const fingers = document.getElementById('answer-fingers');
  const prefix = document.getElementById('answer-prefix');
  const block = document.getElementById('answer-block');
  const subnet = document.getElementById('answer-subnet');

  if (fingers?.value) answer.fingers = Number(fingers.value);
  if (prefix?.value) answer.prefix = Number(prefix.value);
  if (block?.value) answer.block_size = Number(block.value);
  if (subnet?.value) answer.subnet = subnet.value;

  return answer;
}

document.getElementById('submit-game')?.addEventListener('click', async () => {
  const answer = collectAnswer();
  const res = await fetch('/api/game/grade', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ scenario, answer }),
  });
  const data = await res.json();

  feedbackEl.className = 'game-feedback ' + (data.correct ? 'success' : 'error');
  let msg = data.message || (data.correct ? I18N.correct : I18N.incorrect);
  if (data.details?.length) msg += '\n' + data.details.join('\n');
  if (data.badges?.length) {
    const badgeLine = (I18N.badges_earned || '{list}').replace('{list}', data.badges.join(', '));
    msg += '\n' + badgeLine;
  }
  feedbackEl.textContent = msg;

  if (data.correct) {
    setTimeout(() => window.location.reload(), 1500);
  }
});

document.getElementById('hint-game')?.addEventListener('click', async () => {
  const btn = document.getElementById('hint-game');
  if (btn) btn.disabled = true;
  try {
    if (typeof window.askHint === 'function') {
      await window.askHint(scenario, hintEl);
    } else if (typeof window.askTutor === 'function') {
      const q = `Hint for ${scenario.network} needing ${scenario.required_value}`;
      await window.askTutor(q, hintEl);
    }
  } finally {
    if (btn) btn.disabled = false;
  }
});
