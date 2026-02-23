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

// Copy draft content to clipboard
function copyDraft() {
  const el = document.getElementById('draft-content');
  if (!el) return;
  navigator.clipboard.writeText(el.textContent).then(() => {
    const btn = event.target;
    const original = btn.textContent;
    btn.textContent = 'Copied!';
    setTimeout(() => { btn.textContent = original; }, 1500);
  });
}
