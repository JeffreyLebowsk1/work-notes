document.getElementById('advisor-form').addEventListener('submit', async function(e) {
  e.preventDefault();
  const program = document.getElementById('program').value.trim();
  const campus = document.getElementById('campus').value.trim();
  const lastName = document.getElementById('last-name').value.trim();
  const resultCard = document.getElementById('result-card');
  resultCard.style.display = 'none';
  resultCard.innerHTML = '<span style="color:#457b9d">Searching…</span>';
  resultCard.style.display = 'block';

  // Try API call first
  let apiUrl = 'https://cccc.ngrok.app/api/advisor';
  let qrUrl = 'https://cccc.ngrok.app/api/advisor/qr';
  let advisor = null;
  try {
    const resp = await fetch(apiUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ last_name: lastName, campus, program })
    });
    const data = await resp.json();
    if (data.results && data.results.length > 0) {
      advisor = data.results[0];
    }
  } catch (err) {
    advisor = null;
  }

  if (!advisor) {
    resultCard.innerHTML = '<span style="color:#e63946">No advisor found.</span>';
    return;
  }

  // Get QR code
  let qrImg = '';
  try {
    const qrResp = await fetch(qrUrl + '?name=' + encodeURIComponent(advisor.advisor_name || advisor.name));
    const blob = await qrResp.blob();
    const qrBase64 = await new Promise(r => {
      const reader = new FileReader();
      reader.onload = () => r(reader.result);
      reader.readAsDataURL(blob);
    });
    qrImg = `<img src="${qrBase64}" alt="QR" width="140" height="140" class="advisor-qr">`;
  } catch (err) {
    qrImg = '';
  }

  // Build advisor card
  const info = [
    `<div class="advisor-name">${advisor.advisor_name || advisor.name}</div>`,
    `<div class="advisor-meta">${advisor.program || (advisor.programs ? advisor.programs.join(' · ') : '')}</div>`,
    `<div class="advisor-meta">${advisor.campus || (advisor.campuses ? advisor.campuses.join(', ') : '')}</div>`,
    `<div class="advisor-meta">${advisor.office || ''}</div>`,
    `<div class="advisor-meta">${advisor.email ? `<a href='mailto:${advisor.email}'>${advisor.email}</a>` : ''}</div>`,
    qrImg
  ].join('');

  resultCard.innerHTML = info + `
    <div class="advisor-actions">
      <button id="copy-info">Copy Info</button>
      <button id="open-profile">Open Profile</button>
    </div>
  `;

  document.getElementById('copy-info').addEventListener('click', function() {
    const text = `${advisor.advisor_name || advisor.name}\n${advisor.program || (advisor.programs ? advisor.programs.join(' · ') : '')}\n${advisor.campus || (advisor.campuses ? advisor.campuses.join(', ') : '')}\n${advisor.office || ''}\n${advisor.email || ''}`;
    navigator.clipboard.writeText(text);
  });

  document.getElementById('open-profile').addEventListener('click', function() {
    const slug = (advisor.advisor_name || advisor.name || '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
    const url = `https://www.cccc.edu/faculty-staff-directory/${slug}`;
    window.open(url, '_blank');
  });
});
