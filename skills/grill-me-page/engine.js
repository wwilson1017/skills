// grill-me-page engine. The page's config script defines PAGE, VERSION, SECTIONS and Q, and optionally
// MULTI (several people answer), NEXT (topics waiting for this round's answers) and ACKS (false when the
// page's owner cannot write ack files beside it). This file renders the page and gets the answers back.
//
// Transport is decided once at load by probing for a collector beside the page (submit.php, served by
// collect.py or by the PHP adapter):
//   collector  drafts are posted as people work and Go posts the final record; the status box then follows
//              the session: sent -> received -> applied, via ack files the session writes beside the page.
//   copy       nothing answers (a file opened from disk, a static host): Go puts the answers in a box to
//              copy and paste back into the session, with an ANSWERS JSON line build.py --locked reads.
// Drafts are kept in this browser in every mode, so closing the tab loses nothing.
const COLLECT = 'submit.php';
const IS_MULTI = typeof MULTI !== 'undefined' && MULTI;
const WANT_ACKS = typeof ACKS === 'undefined' || ACKS;
const NEXT_UP = typeof NEXT !== 'undefined' && Array.isArray(NEXT) ? NEXT : [];
const LS_KEY = `grill:${PAGE}:v${VERSION}`;
const lsGet = k => { try { return localStorage.getItem(k); } catch (e) { return null; } };
const lsSet = (k, v) => { try { localStorage.setItem(k, v); } catch (e) {} };
const randomId = () => (window.crypto && crypto.getRandomValues)
  ? Array.from(crypto.getRandomValues(new Uint8Array(6)), b => b.toString(16).padStart(2, '0')).join('')
  : Math.random().toString(16).slice(2, 14).padEnd(12, '0');
let CID = lsGet('grill-cid');
if (!/^[0-9a-f]{12}$/.test(CID || '')) { CID = randomId(); lsSet('grill-cid', CID); }
let sentAt = null, sentName = '', sentId = null;
let transport = 'probing';   // probing | collector | copy
let edits = 0;               // bumped on every change a person makes; restores apply only if it has not moved

const $ = (s, r=document) => r.querySelector(s);
const esc = s => String(s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const cloneVis = id => { const t = document.getElementById(id); return t ? t.content.cloneNode(true) : document.createTextNode(''); };
const fmtT = iso => new Date(iso).toLocaleTimeString([], {hour:'numeric', minute:'2-digit'});
const qs = o => '?' + Object.entries(Object.assign({page: PAGE, version: VERSION}, o)).map(([k, v]) => k + '=' + encodeURIComponent(v)).join('&');
const sameVersion = d => d && d.page === PAGE && String(d.version) === String(VERSION);
function mini(text, cls){ const m = $('#saveState'); m.textContent = text; m.className = 'save' + (cls ? ' ' + cls : ''); }

function render(){
  const host = $('#sections'), chips = $('#chips');
  for (const sec of SECTIONS){
    const el = document.createElement('section');
    el.className = 'sec'; el.id = 'sec-' + sec.k;
    el.innerHTML = `<div class="sec-head"><span class="sec-letter">${esc(sec.k)}</span><h2>${esc(sec.t)}</h2></div>` + (sec.take ? `<p class="sec-take">${esc(sec.take)}</p>` : '');
    for (const q of Q.filter(q => q.s === sec.k)){
      const card = document.createElement('div');
      card.className = 'q'; card.id = 'q-' + q.id; card.dataset.id = q.id;
      const type = q.multi ? 'checkbox' : 'radio';
      const opts = q.o.map(([v,label,desc,rec]) =>
        `<label class="opt"><input type="${type}" name="q_${q.id}" value="${esc(v)}"${rec?' data-rec="1"':''}><span><span class="t">${esc(label)}</span>${rec?'<span class="rec">★ recommended</span>':''}${desc?`<span class="d">${esc(desc)}</span>`:''}</span></label>`).join('');
      card.innerHTML = `<div class="q-top"><span class="q-id">${esc(q.id)}</span><div style="flex:1"><h3>${esc(q.t)}</h3>${q.why?`<p class="why">${esc(q.why)}</p>`:''}</div></div>
        <div class="visslot"></div><div class="opts">${opts}</div>
        <label class="lbl" for="a_${esc(q.id)}">Pick an option and add to it here, or just answer in your own words</label>
        <textarea class="answer" id="a_${esc(q.id)}" placeholder="Your answer"></textarea>
        <textarea class="note" placeholder="Notes (optional): double-check that, why, draw it for me…" aria-label="Notes for ${esc(q.id)}"></textarea>`;
      if (q.vis){ const v = document.createElement('div'); v.className = 'vis'; v.appendChild(cloneVis(q.vis)); card.querySelector('.visslot').appendChild(v); }
      el.appendChild(card);
    }
    host.appendChild(el);
    const a = document.createElement('a'); a.className = 'chip'; a.href = '#sec-' + sec.k; a.dataset.sec = sec.k;
    a.innerHTML = `${esc(sec.k)} · ${esc(sec.t)}<span class="c"></span>`; chips.appendChild(a);
  }
  if (NEXT_UP.length){
    const el = document.createElement('section'); el.className = 'sec next'; el.id = 'sec-next';
    el.innerHTML = `<div class="sec-head"><span class="sec-letter">→</span><h2>Waiting on your answers</h2></div>
      <p class="sec-take">These depend on what you decide above, so they come in the next round rather than being guessed at now.</p>
      <ul>${NEXT_UP.map(n => `<li>${esc(n)}</li>`).join('')}</ul>`;
    host.appendChild(el);
  }
  // Any <div data-vis="id"> in the body gets that <template> cloned in.
  document.querySelectorAll('[data-vis]').forEach(d => d.appendChild(cloneVis(d.dataset.vis)));
  if (IS_MULTI) $('#who').style.display = 'block';
  if (!Q.length) { $('.bar').style.display = 'none'; $('#chips').style.display = 'none'; }
}

function state(){
  const answers = {};
  for (const q of Q){
    const card = document.getElementById('q-' + q.id);
    answers[q.id] = {picked: [...card.querySelectorAll('input:checked')].map(i => i.value),
                     answer: card.querySelector('.answer').value.trim(), note: card.querySelector('.note').value.trim()};
  }
  return {answers, my_questions: $('#myQuestions').value.trim(), missing: $('#missing').value.trim(), name: IS_MULTI ? $('#whoName').value.trim() : ''};
}
const answered = a => a.picked.length > 0 || a.answer.length > 0;
const touched = a => answered(a) || a.note.length > 0;

function refresh(){
  const st = state(); let n = 0; const per = {};
  for (const q of Q){
    const t = answered(st.answers[q.id]); if (t) n++;
    document.getElementById('q-' + q.id).classList.toggle('answered', t);
    per[q.s] = per[q.s] || [0, 0]; per[q.s][1]++; if (t) per[q.s][0]++;
  }
  $('#progTxt').textContent = `${n} of ${Q.length} answered · blanks take my recommendation`;
  $('#progFill').style.width = (Q.length ? 100*n/Q.length : 0) + '%';
  document.querySelectorAll('.chip').forEach(c => { const [a,b] = per[c.dataset.sec] || [0,0]; c.querySelector('.c').textContent = ` ${a}/${b}`; c.classList.toggle('done', b > 0 && a === b); });
}

function apply(saved){
  if (!saved || !saved.answers) return false;
  for (const q of Q){
    const a = saved.answers[q.id]; if (!a) continue;
    const card = document.getElementById('q-' + q.id);
    card.querySelectorAll('input').forEach(i => { i.checked = (a.picked || []).includes(i.value); });
    card.querySelector('.answer').value = a.answer || '';
    card.querySelector('.note').value = a.note || '';
  }
  $('#myQuestions').value = saved.my_questions || '';
  $('#missing').value = saved.missing || '';
  if (IS_MULTI && saved.name && !$('#whoName').value.trim()) $('#whoName').value = saved.name;
  return true;
}

// --- keeping the answers: this browser at once, the collector 2.5 s after the last change ---
const keyOf = s => JSON.stringify(s);
let localTimer = null, saveTimer = null, retryTimer = null, lastSaved = '';
function saveLocal(){
  lsSet(LS_KEY, JSON.stringify({saved_at: new Date().toISOString(), sent_at: sentAt, sent_name: sentName, sent_id: sentId, state: state()}));
}
function payload(final){ return Object.assign({page: PAGE, version: VERSION, final, client_id: CID, client_time: new Date().toISOString()}, state()); }
async function post(body){
  const r = await fetch(COLLECT, {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body)});
  const j = await r.json(); if (!j.ok) throw new Error('not ok'); return j;
}
function onChange(){
  edits++;
  refresh();
  clearTimeout(localTimer);
  localTimer = setTimeout(() => { saveLocal(); if (!sentAt) mini(transport === 'collector' ? 'saved on this device ' + fmtT(new Date().toISOString()) : 'kept in this browser'); }, 300);
  if (transport === 'collector') scheduleSave();
}
function scheduleSave(){
  clearTimeout(saveTimer); clearTimeout(retryTimer);
  saveTimer = setTimeout(saveNow, 2500);
}
async function saveNow(){
  const key = keyOf(state());
  if (key === lastSaved) return;
  try {
    await post(payload(false)); lastSaved = key;
    if (sentAt) mini('changed since your send · press Go again', 'warn'); else mini('saved ' + fmtT(new Date().toISOString()));
  } catch (e) {
    mini('saved on this device · not on the page yet, retrying', 'warn');
    retryTimer = setTimeout(saveNow, 30e3);
  }
}

// --- transport ---
async function probe(){
  transport = 'probing';
  try {
    const c = new AbortController(); const t = setTimeout(() => c.abort(), 3000);
    const r = await fetch(COLLECT + qs({acks: 1}), {cache: 'no-store', signal: c.signal}); clearTimeout(t);
    const j = await r.json();
    if (j && typeof j === 'object' && !Array.isArray(j)) { transport = 'collector'; lastAcks = j; } else transport = 'copy';
  } catch (e) { transport = 'copy'; }
  setMode();
}
function setMode(){
  const note = $('#keepNote'), watch = $('#watch');
  if (transport === 'collector'){
    note.textContent = 'Your answers save as you go, on this device and on the page, so you can stop and come back any time. Press Go when you are done; you can press Go again later and the latest send counts.';
    $('#goBottom').textContent = sentAt ? 'Send again' : 'Go: send my answers';
    if (!IS_MULTI && WANT_ACKS) { watch.className = 'watch off'; pollNow(); } else watch.className = 'watch';
    restoreRemote();
  } else {
    note.innerHTML = 'Nothing is sent anywhere: your draft is kept in this browser, and Go puts your answers in a box to copy and paste back into the session that made this page. <a href="#" id="reprobe">Check again for a collector</a>';
    $('#reprobe').addEventListener('click', e => { e.preventDefault(); probe(); });
    $('#goBottom').textContent = 'Go: show my answers to copy';
    watch.className = 'watch'; clearTimeout(ackTimer);
    mini('kept in this browser');
  }
}

// On load: this browser's copy first (instant, works offline). Once a collector is found: the page's newest
// copy for this browser (on a one-person page: from any device), then the status of a Go already sent.
function restoreLocal(){
  let local = null; try { local = JSON.parse(lsGet(LS_KEY) || 'null'); } catch (e) {}
  if (local && local.state && apply(local.state)){
    refresh(); lastSaved = keyOf(state());
    if (local.saved_at) mini('restored from this device · ' + fmtT(local.saved_at));
  }
  if (local && local.sent_at){ sentAt = local.sent_at; sentName = local.sent_name || ''; sentId = local.sent_id || null; }
  return local;
}
let localAt = 0;
function restoreRemote(){
  const e0 = edits;
  fetch(COLLECT + qs(IS_MULTI ? {client: CID} : {}), {cache: 'no-store'}).then(r => r.json()).then(rec => {
    const d = rec && rec.data; if (!sameVersion(d) || edits !== e0) return;
    const at = +new Date(d.client_time || rec.at);
    if (at > localAt + 1000 && apply(d)){ refresh(); lastSaved = keyOf(state()); saveLocal(); mini('restored · ' + fmtT(d.client_time || rec.at)); }
  }).catch(() => {});
  const showSent = () => { if (sentAt) IS_MULTI || !WANT_ACKS ? showSentPlain(sentAt, sentName) : trackAcks(sentAt); };
  fetch(COLLECT + qs(Object.assign({final: 1}, IS_MULTI ? {client: CID} : {})), {cache: 'no-store'}).then(r => r.json()).then(rec => {
    const d = rec && rec.data;
    if (sameVersion(d) && d.final && (!sentAt || new Date(rec.at) > new Date(sentAt))){ sentAt = rec.at; sentName = d.name || ''; sentId = d.submit_id || null; saveLocal(); }
    showSent();
  }).catch(showSent);
}
// A shared page on a new device: once a name is typed and nothing is filled in yet, fetch that name's newest answers.
let nameTimer = null;
const untouched = st => Object.values(st.answers).every(a => !touched(a)) && !st.my_questions && !st.missing;
function nameRestore(){
  if (!IS_MULTI || transport !== 'collector') return;
  clearTimeout(nameTimer);
  nameTimer = setTimeout(async () => {
    const name = $('#whoName').value.trim(); if (name.length < 2 || !untouched(state())) return;
    const e0 = edits;
    try {
      const rec = await (await fetch(COLLECT + qs({name}), {cache: 'no-store'})).json();
      const d = rec && rec.data;
      if (edits !== e0 || $('#whoName').value.trim() !== name) return;   // they kept typing meanwhile
      if (sameVersion(d) && d.client_id !== CID && apply(d)){
        refresh(); lastSaved = keyOf(state()); saveLocal(); mini(`restored ${name}'s answers · ${fmtT(d.client_time || rec.at)}`);
      }
    } catch (e) {}
  }, 800);
}

// The ★ rule, shared with build.py's locked table: ★ is implied only when nothing is picked AND nothing is
// written. An answer in the person's own words stands on its own; a pick plus words shows both.
function summaryText(st){
  const lines = [`${PAGE} v${VERSION} answers — ${new Date().toLocaleString()}` + (st.name ? ` — ${st.name}` : ''), ''];
  for (const q of Q){
    const a = st.answers[q.id];
    const label = v => (q.o.find(o => o[0] === v) || [v, v])[1];
    let pick;
    if (a.picked.length) pick = a.picked.map(label).join('; ');
    else if (a.answer) pick = '(answered in their own words)';
    else if (q.none_rec || !q.o.some(o => o[3])) pick = '(none ticked)';
    else pick = '(blank → recommendation: ' + q.o.filter(o => o[3]).map(o => o[1]).join('; ') + ')';
    lines.push(`${q.id} ${q.t}: ${pick}` + (a.answer ? `\n    answer: ${a.answer}` : '') + (a.note ? `\n    note: ${a.note}` : ''));
  }
  if (st.my_questions) lines.push('', 'MY QUESTIONS:', st.my_questions);
  if (st.missing) lines.push('', 'MISSED / BUILD FIRST:', st.missing);
  return lines.join('\n');
}
const MARKER = 'ANSWERS JSON (for the next round):';
const copyText = body => body.summary_text + '\n\n' + MARKER + '\n' + JSON.stringify(body);

function showSentPlain(at, name){
  const status = $('#status');
  status.className = 'status ack received';
  status.innerHTML = `<b>Sent ✓ ${fmtT(at)}${name ? ' as ' + esc(name) : ''}</b> · kept on the page.`
    + `<span class="late">Changed your mind? Edit anything and press Go again; the latest send counts. Your answers also stay on this device.</span>`;
  mini('sent ✓ ' + fmtT(at), 'ack');
  $('#goBottom').textContent = 'Send again';
}

async function go(){
  clearTimeout(saveTimer); clearTimeout(retryTimer);
  const status = $('#status');
  if (IS_MULTI && !$('#whoName').value.trim()){
    status.className = 'status err'; status.textContent = 'Please type your name first, so your answers are kept under it.';
    $('#whoName').focus(); $('#whoName').scrollIntoView({behavior: 'smooth', block: 'center'}); return;
  }
  const btns = [$('#goTop'), $('#goBottom')]; btns.forEach(b => b.disabled = true);
  const body = payload(true);
  body.submit_id = randomId();
  body.summary_text = summaryText(body);
  body.questions = Q.map(q => ({id: q.id, t: q.t, o: q.o.map(o => [o[0], o[1], !!o[3]]), none_rec: !!q.none_rec}));
  const box = $('#summary');
  if (transport === 'collector'){
    status.className = 'status ack sent'; status.innerHTML = '<span class="live"></span><b>Sending…</b>';
    box.value = body.summary_text; box.style.display = 'block'; $('#copyBtn').style.display = 'inline-block';
    try {
      const j = await post(body);
      lastSaved = keyOf(state()); sentAt = j.at; sentName = body.name || ''; sentId = body.submit_id; saveLocal();
      if (IS_MULTI || !WANT_ACKS) showSentPlain(sentAt, sentName); else trackAcks(j.at);
    } catch (e) {
      saveLocal();
      box.value = copyText(body);
      status.className = 'status err';
      status.textContent = 'Not sent (no connection?). Nothing is lost: your answers are saved on this device. Press Go again in a moment; if it keeps failing, copy the box below and send it to whoever gave you this page.';
      mini('not sent · saved on this device', 'warn');
    }
  } else {
    box.value = copyText(body); box.style.display = 'block'; $('#copyBtn').style.display = 'inline-block';
    let copied = false;
    try { await navigator.clipboard.writeText(box.value); copied = true; } catch (e) {}
    status.className = 'status ok';
    status.textContent = copied ? 'Copied ✓ Paste it into the session that made this page. It is also in the box below.'
                                : 'Your answers are in the box below. Copy it and paste it into the session that made this page.';
    saveLocal();
  }
  btns.forEach(b => b.disabled = false);
  $('#final').scrollIntoView({behavior: 'smooth', block: 'start'});
}

function takeRecs(){
  for (const q of Q){
    if (q.none_rec) continue;
    const card = document.getElementById('q-' + q.id);
    if (card.querySelector('input:checked') || card.querySelector('.answer').value.trim()) continue;
    card.querySelectorAll('input[data-rec]').forEach(i => i.checked = true);
  }
  onChange();
}
// A second click on the selected radio clears it, so a person can switch to an answer in their own words.
document.addEventListener('pointerdown', e => {
  const lab = e.target.closest('label.opt'); const i = lab && lab.querySelector('input[type=radio]');
  if (i) i.dataset.was = i.checked ? '1' : '';
});
document.addEventListener('click', e => {
  const i = e.target; if (!(i instanceof HTMLInputElement) || i.type !== 'radio' || i.dataset.was !== '1') return;
  i.dataset.was = ''; setTimeout(() => { i.checked = false; onChange(); }, 0);
});

// After Go on a one-person page the status box follows the session: sent (amber) -> received (green) -> applied
// (green, big check). Acks and the watcher heartbeat (`alive`) come from submit.php?acks=1, written beside the
// page by the session (collect.py or its hosted equivalent). Polls every 60 s before Go (for the watcher line),
// every 10 s after Go (every 60 s after 2 h), and at once whenever the page comes back into view.
let ackTimer = null, polling = false, lastAcks = {}, lastErr = false;
const WATCH_STALE = 3*60e3;
const watching = () => { const a = lastAcks.alive; return !!a && Date.now() - new Date(a.at) < WATCH_STALE; };
function watchText(){
  if (lastErr) return 'could not reach the collector, retrying…';
  if (watching()) return `a session is watching this page · last seen ${fmtT(lastAcks.alive.at)}`;
  return 'no session is watching right now · your answers are kept here and picked up when one looks';
}
function showAck(stage, at, msg){
  const late = stage !== 'applied' && Date.now() - new Date(sentAt) > 2*3600e3;
  const line = {
    sent: `<span class="live"></span><b>Sent ✓ ${fmtT(at)}</b> · waiting for the session to pick this up…`,
    received: `<b>The session has your answers ✓ ${fmtT(at)}</b>`,
    applied: `<span class="bigcheck">✓</span><b>All applied ${fmtT(at)}</b>`}[stage];
  const status = $('#status');
  status.className = 'status ack ' + stage;
  const dash = $('a.dash');  // an optional "all your pages" link in the bar
  const notes = [];
  if (stage === 'sent') notes.push(watchText()); else if (lastErr) notes.push(watchText());
  if (late) notes.push('Still waiting; the session may be busy. This page keeps checking.');
  status.innerHTML = line + (msg ? ` · ${esc(msg)}` : '') + (dash ? ` · <a href="${dash.href}">All your pages →</a>` : '')
    + (stage === 'applied' ? '' : ' <button type="button" class="mini" id="ackRefresh">Refresh status</button>')
    + notes.map(n => `<span class="late">${esc(n)}</span>`).join('');
  const btn = $('#ackRefresh'); if (btn) btn.addEventListener('click', pollNow);
  mini({sent: 'sent ✓ waiting…', received: 'received ✓', applied: 'all applied ✓'}[stage], 'ack');
}
async function pollAcks(){
  if (polling || transport !== 'collector' || IS_MULTI || !WANT_ACKS) return; polling = true; clearTimeout(ackTimer);
  let acks = null;
  try { acks = await (await fetch(COLLECT + qs({acks: 1}), {cache: 'no-store'})).json(); } catch (e) {}
  polling = false;
  lastErr = !acks; if (acks) lastAcks = acks;   // a failed fetch keeps the last known state and says so
  const w = $('#watch'); if (w) { w.className = 'watch ' + (lastErr ? 'err' : watching() ? 'on' : 'off'); w.textContent = watchText(); }
  if (sentAt){
    // An ack counts only for this page and version, and only for the send it answers: by submit_id when the
    // send carried one; for a send from before submit ids, not older than the Go (30 s clock slack).
    const mine = s => { const a = lastAcks[s]; if (!a || a.page !== PAGE || String(a.version) !== String(VERSION)) return null;
      return (sentId ? a.submit_id === sentId : new Date(a.at) >= new Date(sentAt) - 30e3) ? a : null; };
    const ap = mine('applied'), rc = mine('received');
    if (ap) { showAck('applied', ap.at, ap.message); return; }
    if (rc) showAck('received', rc.at, rc.message); else showAck('sent', sentAt, '');
  }
  ackTimer = setTimeout(pollAcks, !sentAt || Date.now() - new Date(sentAt) > 2*3600e3 ? 60e3 : 10e3);
}
function pollNow(){ clearTimeout(ackTimer); pollAcks(); }
function trackAcks(at){ sentAt = at; $('#goBottom').textContent = 'Send again'; showAck('sent', at, ''); pollNow(); }

render();
document.addEventListener('input', onChange);
document.addEventListener('change', onChange);
$('#whoName').addEventListener('input', nameRestore);
$('#takeRecs').addEventListener('click', takeRecs);
$('#goTop').addEventListener('click', go);
$('#goBottom').addEventListener('click', go);
$('#copyBtn').addEventListener('click', async () => {
  const box = $('#summary'); box.select();
  try { await navigator.clipboard.writeText(box.value); $('#copyBtn').textContent = 'Copied'; }
  catch (e) { try { document.execCommand('copy'); $('#copyBtn').textContent = 'Copied'; } catch (_) { $('#copyBtn').textContent = 'Select the text and copy it'; } }
});
refresh();
document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'visible') pollNow(); });
window.addEventListener('focus', pollNow);
window.addEventListener('pageshow', pollNow);
// Restore after the page's own add-ons (registered earlier in the body) have wrapped state/apply.
function start(){ const local = restoreLocal(); localAt = local && local.saved_at ? +new Date(local.saved_at) : 0; probe(); }
if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start); else start();
