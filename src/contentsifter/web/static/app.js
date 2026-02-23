// ContentSifter minimal JS

// Auto-dismiss flash messages after 4 seconds
document.addEventListener('htmx:afterSettle', () => {
  document.querySelectorAll('[data-flash]').forEach(el => {
    setTimeout(() => {
      el.style.opacity = '0';
      el.style.transition = 'opacity 0.3s ease';
      setTimeout(() => el.remove(), 300);
    }, 4000);
  });
});

// Also run on initial page load
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('[data-flash]').forEach(el => {
    setTimeout(() => {
      el.style.opacity = '0';
      el.style.transition = 'opacity 0.3s ease';
      setTimeout(() => el.remove(), 300);
    }, 4000);
  });
});

// Dropzone drag-and-drop handling
function initDropzone(dropzoneId, fileInputId) {
  const dropzone = document.getElementById(dropzoneId);
  const fileInput = document.getElementById(fileInputId);
  if (!dropzone || !fileInput) return;

  ['dragenter', 'dragover'].forEach(event => {
    dropzone.addEventListener(event, e => {
      e.preventDefault();
      dropzone.classList.add('drag-over');
    });
  });

  ['dragleave', 'drop'].forEach(event => {
    dropzone.addEventListener(event, e => {
      e.preventDefault();
      dropzone.classList.remove('drag-over');
    });
  });

  dropzone.addEventListener('drop', e => {
    fileInput.files = e.dataTransfer.files;
    fileInput.dispatchEvent(new Event('change', { bubbles: true }));
  });

  dropzone.addEventListener('click', () => fileInput.click());
}

// Search result expand/collapse
function toggleDetail(id, url) {
  const detail = document.getElementById('detail-' + id);
  const chevron = document.getElementById('chevron-' + id);
  if (!detail) return;

  const isExpanded = detail.classList.contains('expanded');
  detail.classList.toggle('expanded');
  if (chevron) chevron.classList.toggle('rotated');

  // Fetch full content on first expand
  if (!isExpanded && !detail.dataset.loaded && url) {
    htmx.ajax('GET', url, {target: '#detail-' + id, swap: 'innerHTML'});
    detail.dataset.loaded = 'true';
  }
}

// Category tab switching
function selectCategory(button, category) {
  document.querySelectorAll('.browse-tab').forEach(b => b.classList.remove('active'));
  button.classList.add('active');
  document.getElementById('category-filter').value = category;
}

// Fill search input from suggestion chip and trigger search
function searchFor(term) {
  const input = document.getElementById('search-input');
  if (!input) return;
  input.value = term;
  htmx.trigger(input, 'search');
}

// Copy draft content to clipboard
function copyDraft(button) {
  const el = document.getElementById('draft-content');
  if (!el || !button) return;
  navigator.clipboard.writeText(el.textContent).then(() => {
    showCopyFeedback(button);
  });
}

// Shared copy feedback animation
function showCopyFeedback(btn) {
  const original = btn.innerHTML;
  btn.innerHTML = '<svg class="inline w-3.5 h-3.5 -mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg> Copied!';
  btn.classList.add('success');
  setTimeout(() => {
    btn.innerHTML = original;
    btn.classList.remove('success');
  }, 1500);
}

// Saved drafts: expand/collapse
function toggleDraft(id, url) {
  const detail = document.getElementById('draft-detail-' + id);
  const chevron = document.getElementById('draft-chevron-' + id);
  if (!detail) return;

  const isExpanded = detail.classList.contains('expanded');
  detail.classList.toggle('expanded');
  if (chevron) chevron.classList.toggle('rotated');

  if (!isExpanded && !detail.dataset.loaded && url) {
    htmx.ajax('GET', url, {target: '#draft-detail-' + id, swap: 'innerHTML'});
    detail.dataset.loaded = 'true';
  }
}

// Saved drafts: copy body from expanded detail
function copyDraftBody(id, button) {
  const detail = document.getElementById('draft-detail-' + id);
  if (!detail || !detail.dataset.loaded) return;
  const textEl = detail.querySelector('.whitespace-pre-wrap');
  if (!textEl || !button) return;
  navigator.clipboard.writeText(textEl.textContent).then(() => {
    showCopyFeedback(button);
  });
}

// Saved drafts: delete with fade-out
function deleteDraft(id, slug, filename) {
  if (!confirm('Delete this draft?')) return;
  const card = document.getElementById('draft-' + id);
  if (card) {
    card.style.transition = 'opacity 0.25s ease, transform 0.25s ease';
    card.style.opacity = '0';
    card.style.transform = 'translateX(8px)';
  }
  setTimeout(() => {
    htmx.ajax('DELETE', '/' + slug + '/drafts/' + filename, {target: '#draft-' + id, swap: 'outerHTML'});
  }, 250);
}
