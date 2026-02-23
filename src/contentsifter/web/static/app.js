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

// Copy draft content to clipboard (finds content within the same card)
function copyDraft(button) {
  var card = button.closest('.draft-result-card');
  var el = card ? card.querySelector('.draft-content') : document.getElementById('draft-content');
  if (!el || !button) return;
  navigator.clipboard.writeText(el.textContent).then(() => {
    showCopyFeedback(button);
  });
}

// Shared feedback animation (checkmark + temporary label, then restore)
function showCopyFeedback(btn) {
  const original = btn.innerHTML;
  btn.innerHTML = '<svg class="inline w-3.5 h-3.5 -mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg> Copied!';
  btn.classList.add('success');
  setTimeout(() => {
    btn.innerHTML = original;
    btn.classList.remove('success');
  }, 1500);
}

// Save draft to disk, then show checkmark and disable button
function saveDraft(btn, slug, formatType, topic) {
  if (btn.disabled) return;
  btn.disabled = true;

  var card = btn.closest('.draft-result-card');
  var el = card ? card.querySelector('.draft-content') : null;
  if (!el) { btn.disabled = false; return; }

  var formData = new FormData();
  formData.append('content', el.textContent);
  formData.append('topic', topic);
  formData.append('format_type', formatType);

  fetch('/' + slug + '/generate/save', { method: 'POST', body: formData })
    .then(function(resp) { return resp.text(); })
    .then(function(html) {
      // Show save result message in the same card
      var target = card.querySelector('.save-result');
      if (target) target.innerHTML = html;

      // Animate button to "Saved!" and keep it disabled
      btn.innerHTML = '<svg class="inline w-3.5 h-3.5 -mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg> Saved!';
      btn.classList.add('success');
      btn.classList.remove('hover:text-indigo-800');
      btn.style.cursor = 'default';
    })
    .catch(function() {
      btn.disabled = false;
    });
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

// ===== Drafts: Batch Selection =====

function updateBatchToolbar() {
  var checkboxes = document.querySelectorAll('.draft-checkbox');
  var checked = document.querySelectorAll('.draft-checkbox:checked');
  var toolbar = document.getElementById('batch-toolbar');
  var countEl = document.getElementById('batch-count');
  var selectAll = document.getElementById('select-all-checkbox');

  if (!toolbar) return;

  if (checked.length > 0) {
    toolbar.classList.remove('hidden');
    countEl.textContent = checked.length + ' selected';
  } else {
    toolbar.classList.add('hidden');
  }

  // Update "select all" checkbox state
  if (selectAll) {
    selectAll.checked = checkboxes.length > 0 && checked.length === checkboxes.length;
    selectAll.indeterminate = checked.length > 0 && checked.length < checkboxes.length;
  }
}

function toggleSelectAllDrafts(selectAllCheckbox) {
  var checkboxes = document.querySelectorAll('.draft-checkbox');
  checkboxes.forEach(function(cb) { cb.checked = selectAllCheckbox.checked; });
  updateBatchToolbar();
}

function batchDeleteDrafts(slug) {
  var checked = document.querySelectorAll('.draft-checkbox:checked');
  if (checked.length === 0) return;

  if (!confirm('Delete ' + checked.length + ' draft' + (checked.length > 1 ? 's' : '') + '?')) return;

  // Build form data with all selected filenames
  var formData = new FormData();
  checked.forEach(function(cb) {
    formData.append('filenames', cb.dataset.filename);
  });

  // htmx.ajax doesn't support FormData with repeated keys, so use fetch
  fetch('/' + slug + '/drafts/batch-delete', {
    method: 'POST',
    body: formData,
  })
  .then(function(response) { return response.text(); })
  .then(function(html) {
    document.getElementById('drafts-container').innerHTML = html;
    // Update the count in the header
    var remaining = document.querySelectorAll('.draft-checkbox').length;
    var countEl = document.querySelector('#drafts-count, .text-sm.text-zinc-500');
    // Trigger flash auto-dismiss
    document.querySelectorAll('[data-flash]').forEach(function(el) {
      setTimeout(function() {
        el.style.opacity = '0';
        el.style.transition = 'opacity 0.3s ease';
        setTimeout(function() { el.remove(); }, 300);
      }, 4000);
    });
  });
}

// ===== Content Planner: Drag & Drop =====

function handleSlotDragOver(event) {
  event.preventDefault();
  event.currentTarget.classList.add('drag-over');
}

function handleSlotDragLeave(event) {
  event.currentTarget.classList.remove('drag-over');
}

function handleSlotDrop(event) {
  event.preventDefault();
  event.currentTarget.classList.remove('drag-over');

  const filename = event.dataTransfer.getData('text/draft-filename');
  const sourceDayName = event.dataTransfer.getData('text/card-day');
  const slot = event.currentTarget;
  const dayName = slot.dataset.day;
  const slug = slot.dataset.slug;
  const week = slot.dataset.week;

  if (filename && dayName) {
    // Dropping a saved draft onto a slot
    htmx.ajax('POST',
      '/' + slug + '/planner/slot/' + dayName + '/assign-draft',
      {
        target: '#slot-' + dayName,
        swap: 'innerHTML',
        values: { filename: filename, week: week }
      }
    );
  } else if (sourceDayName && sourceDayName !== dayName) {
    // Swapping cards between slots — swap via both updates
    // For now, just notify user
    console.log('Card swap from', sourceDayName, 'to', dayName, '(not yet supported)');
  }
}

function handleDraftDragStart(event) {
  event.dataTransfer.setData('text/draft-filename', event.target.dataset.filename);
  event.dataTransfer.effectAllowed = 'copy';
  event.target.classList.add('dragging');
}

function handleDraftDragEnd(event) {
  event.target.classList.remove('dragging');
  document.querySelectorAll('.drag-over').forEach(function(el) { el.classList.remove('drag-over'); });
}

function handleCardDragStart(event) {
  event.dataTransfer.setData('text/card-day', event.target.dataset.day);
  event.dataTransfer.effectAllowed = 'move';
  event.target.classList.add('dragging');
}

function handleCardDragEnd(event) {
  event.target.classList.remove('dragging');
  document.querySelectorAll('.drag-over').forEach(function(el) { el.classList.remove('drag-over'); });
}

// ===== Content Planner: Side Panel =====

function openSidePanel(slug, dayName, weekStart) {
  var panel = document.getElementById('side-panel');
  var overlay = document.getElementById('side-panel-overlay');
  panel.classList.remove('hidden');
  if (overlay) overlay.classList.remove('hidden');

  htmx.ajax('GET',
    '/' + slug + '/planner/side-panel/' + dayName + '?week=' + weekStart,
    { target: '#side-panel-content', swap: 'innerHTML' }
  );

  var grid = document.getElementById('planner-grid');
  if (grid) grid.classList.add('panel-open');
}

function closeSidePanel() {
  var panel = document.getElementById('side-panel');
  var overlay = document.getElementById('side-panel-overlay');
  panel.classList.add('hidden');
  if (overlay) overlay.classList.add('hidden');

  var grid = document.getElementById('planner-grid');
  if (grid) grid.classList.remove('panel-open');
}

function copySlotContent() {
  var textarea = document.querySelector('.planner-side-panel textarea[name="content"]');
  if (!textarea) return;
  navigator.clipboard.writeText(textarea.value).then(function() {
    // Brief feedback
    var btn = document.querySelector('.planner-side-panel .action-btn');
    if (btn) showCopyFeedback(btn);
  });
}

// Planner side panel: show "Saved!" feedback after htmx save succeeds
document.addEventListener('htmx:afterRequest', function(event) {
  var btn = document.getElementById('planner-save-btn');
  if (!btn || event.detail.elt !== btn.closest('form')) return;
  if (!event.detail.successful) return;

  var origHTML = btn.innerHTML;
  btn.innerHTML = '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg> Saved!';
  btn.classList.remove('bg-indigo-600', 'hover:bg-indigo-700');
  btn.classList.add('bg-emerald-600');
  setTimeout(function() {
    btn.innerHTML = origHTML;
    btn.classList.remove('bg-emerald-600');
    btn.classList.add('bg-indigo-600', 'hover:bg-indigo-700');
  }, 1500);
});

// ===== Content Planner: Drafts Drawer =====

function toggleDraftsDrawer() {
  var drawer = document.getElementById('drafts-drawer');
  var chevron = document.getElementById('drawer-chevron');
  if (!drawer) return;
  drawer.classList.toggle('expanded');
  if (chevron) chevron.classList.toggle('rotated');
}
