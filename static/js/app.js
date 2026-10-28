document.addEventListener('DOMContentLoaded', () => {
  const messageForm = document.getElementById('messageForm');
  const messageInput = document.getElementById('messageInput');
  const feedContainer = document.getElementById('feedContainer');
  const feedCount = document.getElementById('feedCount');
  const clearBtn = document.getElementById('clearBtn');
  const refreshBtn = document.getElementById('refreshBtn');
  const tabButtons = document.querySelectorAll('.tab-control-btn');
  const tabPanels = document.querySelectorAll('.schematic-panel');
  const presetButtons = document.querySelectorAll('.preset-btn');

  // Submit message via AJAX
  if (messageForm) {
    messageForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const message = messageInput.value.trim();
      if (!message) return;

      try {
        const response = await fetch('/submit', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ new_message: message })
        });

        const data = await response.json();
        if (response.ok) {
          // Prepend new item to feed
          const row = document.createElement('div');
          row.className = 'feed-row';
          row.innerHTML = `
            <div class="feed-row-meta">
              <span class="feed-tag mono">LOG</span>
              <span class="mono">${data.created_at || 'Just now'}</span>
            </div>
            <div class="feed-message">${escapeHtml(data.message)}</div>
          `;
          feedContainer.prepend(row);
          messageInput.value = '';
          updateMessageCount(1);
        } else {
          alert(data.error || 'Failed to submit message');
        }
      } catch (err) {
        console.error('Submission error:', err);
        alert('Error connecting to the application server.');
      }
    });
  }

  // Handle Preset Chips
  presetButtons.forEach((btn) => {
    btn.addEventListener('click', () => {
      messageInput.value = btn.dataset.text || btn.textContent.trim();
      messageInput.focus();
    });
  });

  // Handle Clear Messages
  if (clearBtn) {
    clearBtn.addEventListener('click', async (e) => {
      e.preventDefault();
      if (!confirm('Clear all deployment records from the database?')) return;
      try {
        const res = await fetch('/api/clear', { method: 'POST' });
        if (res.ok) {
          feedContainer.innerHTML = '<div class="feed-row"><div class="feed-message" style="color:var(--text-muted);">No deployment records logged yet.</div></div>';
          if (feedCount) feedCount.textContent = '0 RECORDS';
        }
      } catch (err) {
        console.error('Error clearing records:', err);
      }
    });
  }

  // Handle Refresh Messages
  if (refreshBtn) {
    refreshBtn.addEventListener('click', async (e) => {
      e.preventDefault();
      try {
        const res = await fetch('/api/messages');
        const data = await res.json();
        if (res.ok && data.messages) {
          renderFeed(data.messages);
        }
      } catch (err) {
        console.error('Error refreshing records:', err);
      }
    });
  }

  function renderFeed(messages) {
    if (!feedContainer) return;
    if (messages.length === 0) {
      feedContainer.innerHTML = '<div class="feed-row"><div class="feed-message" style="color:var(--text-muted);">No deployment records logged yet.</div></div>';
      if (feedCount) feedCount.textContent = '0 RECORDS';
      return;
    }

    feedContainer.innerHTML = messages
      .map(
        (m) => `
        <div class="feed-row">
          <div class="feed-row-meta">
            <span class="feed-tag mono">LOG #${m.id}</span>
            <span class="mono">${m.created_at || ''}</span>
          </div>
          <div class="feed-message">${escapeHtml(m.message)}</div>
        </div>
      `
      )
      .join('');

    if (feedCount) feedCount.textContent = `${messages.length} RECORDS`;
  }

  function updateMessageCount(delta) {
    if (!feedCount) return;
    const current = parseInt(feedCount.textContent) || 0;
    feedCount.textContent = `${Math.max(0, current + delta)} RECORDS`;
  }

  // Handle Schematic Tab Navigation
  tabButtons.forEach((btn) => {
    btn.addEventListener('click', () => {
      tabButtons.forEach((b) => b.classList.remove('active'));
      tabPanels.forEach((p) => p.classList.remove('active'));

      btn.classList.add('active');
      const targetId = btn.dataset.tab;
      const targetPanel = document.getElementById(targetId);
      if (targetPanel) targetPanel.classList.add('active');
    });
  });

  function escapeHtml(str) {
    if (!str) return '';
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }
});
