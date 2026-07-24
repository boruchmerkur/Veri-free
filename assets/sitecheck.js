/* Veri-Free — free site check (AI searchability + SEO)
   Calls the checkmysite audit backend (server-side fetch of the target, so it
   works cross-origin), then shows only the AI-assistant-visibility and SEO
   checks. No backend on this site; connect-src must allow dreamsitedesign.com. */
(function () {
  'use strict';
  var form = document.getElementById('scForm');
  if (!form) return;
  var input = document.getElementById('scInput'),
      btn = document.getElementById('scBtn'),
      statusEl = document.getElementById('scStatus'),
      results = document.getElementById('scResults'),
      foot = document.getElementById('scFoot');
  var API = 'https://dreamsitedesign.com/api/audit';
  var ICO = { pass: '✓', warn: '!', fail: '✕' };
  // Localized homepages set window.SC_STRINGS before this script loads.
  var S = Object.assign({
    enter: 'Enter a web address like yourdomain.com',
    checking: 'Reading {d} — checking AI access and SEO…',
    err: 'Couldn’t complete the check — try again.',
    unreach: 'Couldn’t reach the checker — try again in a moment.',
    issues_1: '{n} issue to fix', issues_n: '{n} issues to fix',
    review: '{n} to review', passed: 'all {n} checks passed ✓'
  }, window.SC_STRINGS || {});

  function clean(h) {
    return h.replace(/^https?:\/\//i, '').replace(/\/.*/, '').replace(/\s/g, '').toLowerCase().trim();
  }
  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
    });
  }

  var busy = false;
  form.addEventListener('submit', function (e) {
    e.preventDefault();
    var d = clean(input.value);
    if (!d || d.indexOf('.') < 1) {
      statusEl.hidden = false; statusEl.className = 'sc-status err';
      statusEl.textContent = S.enter;
      return;
    }
    if (busy) return;
    busy = true; btn.disabled = true;
    var lbl = btn.textContent; btn.textContent = '…';
    statusEl.hidden = false; statusEl.className = 'sc-status';
    statusEl.textContent = S.checking.replace('{d}', d);
    results.innerHTML = ''; foot.hidden = true;

    fetch(API, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url: d })
    })
      .then(function (r) { return r.json().then(function (j) { return { ok: r.ok, j: j }; }); })
      .then(function (res) {
        var j = res.j;
        if (!res.ok || !j || j.error) {
          statusEl.className = 'sc-status err';
          statusEl.textContent = (j && j.error) ? j.error : S.err;
          return;
        }
        var items = (j.checks || []).filter(function (c) { return c.cat === 'AI Search' || c.cat === 'SEO'; });
        // AI Search first, then SEO
        items.sort(function (a, b) { return (a.cat === 'AI Search' ? 0 : 1) - (b.cat === 'AI Search' ? 0 : 1); });
        var fails = items.filter(function (c) { return c.status === 'fail'; }).length;
        var warns = items.filter(function (c) { return c.status === 'warn'; }).length;
        var passed = items.filter(function (c) { return c.status === 'pass'; }).length;
        statusEl.className = 'sc-status';
        statusEl.innerHTML = '<b>' + esc(j.host || d) + '</b> — ' +
          (fails ? (fails === 1 ? S.issues_1 : S.issues_n).replace('{n}', fails)
                 : warns ? S.review.replace('{n}', warns)
                         : S.passed.replace('{n}', passed));
        results.innerHTML = items.map(function (c) {
          return '<div class="sc-row ' + c.status + '"><span class="sc-ico">' + ICO[c.status] + '</span>' +
            '<div class="sc-txt"><div class="sc-rl"><b>' + esc(c.label) + '</b>' +
            '<span class="sc-tag">' + esc(c.cat) + '</span></div>' +
            '<div class="sc-d">' + esc(c.detail) + '</div></div></div>';
        }).join('');
        foot.hidden = false;
      })
      .catch(function () {
        statusEl.className = 'sc-status err';
        statusEl.textContent = S.unreach;
      })
      .then(function () { busy = false; btn.disabled = false; btn.textContent = lbl; });
  });
})();
