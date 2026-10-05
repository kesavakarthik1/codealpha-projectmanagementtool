/**
 * ProjectFlow – main.js
 * Vanilla JavaScript only. No frameworks.
 * CodeAlpha Task 3 – Project Management Tool
 */

(function () {
  'use strict';

  // =========================================================================
  // 1. DOM-ready helper
  // =========================================================================
  function ready(fn) {
    if (document.readyState !== 'loading') {
      fn();
    } else {
      document.addEventListener('DOMContentLoaded', fn);
    }
  }

  // =========================================================================
  // 2. Mobile Navigation (hamburger toggle)
  // =========================================================================
  function initNavigation() {
    var hamburger = document.getElementById('navHamburger');
    var navLinks  = document.getElementById('navLinks');
    if (!hamburger || !navLinks) return;

    hamburger.addEventListener('click', function () {
      var isOpen = navLinks.classList.toggle('open');
      hamburger.classList.toggle('open', isOpen);
      hamburger.setAttribute('aria-expanded', String(isOpen));
    });

    // Close nav when a link is clicked (mobile)
    navLinks.querySelectorAll('a, button[type="submit"]').forEach(function (el) {
      el.addEventListener('click', function () {
        navLinks.classList.remove('open');
        hamburger.classList.remove('open');
        hamburger.setAttribute('aria-expanded', 'false');
      });
    });

    // Close nav when clicking outside
    document.addEventListener('click', function (e) {
      if (!hamburger.contains(e.target) && !navLinks.contains(e.target)) {
        navLinks.classList.remove('open');
        hamburger.classList.remove('open');
        hamburger.setAttribute('aria-expanded', 'false');
      }
    });
  }

  // =========================================================================
  // 3. User Dropdown Menu
  // =========================================================================
  function initUserDropdown() {
    var btn      = document.getElementById('userMenuBtn');
    var dropdown = document.getElementById('userDropdown');
    if (!btn || !dropdown) return;

    btn.addEventListener('click', function (e) {
      e.stopPropagation();
      var isOpen = dropdown.classList.toggle('open');
      btn.setAttribute('aria-expanded', String(isOpen));
    });

    // Close on outside click
    document.addEventListener('click', function (e) {
      if (!btn.contains(e.target) && !dropdown.contains(e.target)) {
        dropdown.classList.remove('open');
        btn.setAttribute('aria-expanded', 'false');
      }
    });

    // Close on Escape
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') {
        dropdown.classList.remove('open');
        btn.setAttribute('aria-expanded', 'false');
      }
    });
  }

  // =========================================================================
  // 4. Auto-dismiss Messages
  // =========================================================================
  function initMessages() {
    var messages = document.querySelectorAll('.message');
    messages.forEach(function (msg) {
      // Auto-dismiss success/info messages after 5 seconds
      var tag = msg.className;
      if (tag.indexOf('message-success') !== -1 || tag.indexOf('message-info') !== -1) {
        setTimeout(function () {
          dismissMessage(msg);
        }, 5000);
      }
    });
  }

  function dismissMessage(msg) {
    msg.style.transition = 'opacity 0.3s, transform 0.3s';
    msg.style.opacity    = '0';
    msg.style.transform  = 'translateY(-8px)';
    setTimeout(function () {
      if (msg.parentNode) msg.parentNode.removeChild(msg);
    }, 320);
  }

  // =========================================================================
  // 5. Character Counter (comment textarea and other textareas)
  // =========================================================================
  function initCharCounters() {
    // Comment textarea (task_detail.html has its own inline script,
    // but we handle any textarea with data-maxlength here too)
    document.querySelectorAll('textarea[data-maxlength]').forEach(function (ta) {
      var max     = parseInt(ta.getAttribute('data-maxlength'), 10);
      var counter = document.createElement('span');
      counter.className = 'char-counter';
      counter.textContent = '0 / ' + max;
      ta.parentNode.insertBefore(counter, ta.nextSibling);

      ta.addEventListener('input', function () {
        var len = ta.value.length;
        counter.textContent = len + ' / ' + max;
        counter.style.color = len > max * 0.9 ? 'var(--clr-danger)' : '';
      });
    });

    // Main comment box (identified by class from task_detail template)
    var commentBox     = document.querySelector('.comment-form textarea');
    var commentCounter = document.getElementById('commentCounter');
    if (commentBox && commentCounter) {
      var MAX = 2000;
      commentBox.addEventListener('input', function () {
        var len = commentBox.value.length;
        commentCounter.textContent = len + ' / ' + MAX;
        commentCounter.style.color = len > MAX * 0.9 ? 'var(--clr-danger)' : '';
        if (len > MAX) {
          commentBox.value = commentBox.value.substring(0, MAX);
          commentCounter.textContent = MAX + ' / ' + MAX;
        }
      });
    }
  }

  // =========================================================================
  // 6. Form validation feedback (client-side hints, server is source of truth)
  // =========================================================================
  function initFormFeedback() {
    // Highlight fields that already have server-side errors on load
    document.querySelectorAll('.form-errors').forEach(function (errList) {
      var formGroup = errList.closest('.form-group');
      if (formGroup) {
        var input = formGroup.querySelector('input, textarea, select');
        if (input) {
          input.style.borderColor = 'var(--clr-danger)';
          input.addEventListener('input', function () {
            input.style.borderColor = '';
          }, { once: true });
        }
      }
    });

    // Prevent double-submit on forms
    document.querySelectorAll('form').forEach(function (form) {
      // Skip logout and status-change forms (they should be instant)
      if (form.classList.contains('card-status-form')) return;
      if (form.classList.contains('inline-form')) return;

      form.addEventListener('submit', function () {
        var submitBtn = form.querySelector('button[type="submit"]');
        if (submitBtn && !submitBtn.disabled) {
          submitBtn.disabled = true;
          submitBtn.textContent = 'Saving…';
          // Re-enable after 8s as fallback in case of client-side issue
          setTimeout(function () {
            submitBtn.disabled = false;
          }, 8000);
        }
      });
    });
  }

  // =========================================================================
  // 7. Kanban Board – Task Card Filter (UI-only, refines already-filtered
  //    server result by searching title text client-side)
  // =========================================================================
  function initBoardSearch() {
    var boardEl = document.getElementById('kanbanBoard');
    if (!boardEl) return;

    // Build a live text filter input and inject it into the filter bar
    var filterForm = document.querySelector('.filter-form');
    if (!filterForm) return;

    var wrapper = document.createElement('div');
    wrapper.className = 'filter-group';

    var label = document.createElement('label');
    label.htmlFor = 'boardTaskSearch';
    label.className = 'filter-label';
    label.textContent = 'Find task:';

    var input = document.createElement('input');
    input.type = 'text';
    input.id   = 'boardTaskSearch';
    input.placeholder = 'Filter by title…';
    input.className   = 'form-control form-control-sm';
    input.style.width = '180px';
    input.setAttribute('autocomplete', 'off');

    wrapper.appendChild(label);
    wrapper.appendChild(input);
    filterForm.appendChild(wrapper);

    input.addEventListener('input', function () {
      var query = input.value.trim().toLowerCase();
      var cards = boardEl.querySelectorAll('.task-card');

      cards.forEach(function (card) {
        var titleEl = card.querySelector('.task-card-title');
        var text    = titleEl ? titleEl.textContent.toLowerCase() : '';
        var match   = !query || text.indexOf(query) !== -1;
        card.style.display = match ? '' : 'none';
      });

      // Update column counts after filtering
      boardEl.querySelectorAll('.kanban-col').forEach(function (col) {
        var visible = col.querySelectorAll('.task-card:not([style*="display: none"])').length;
        var countEl = col.querySelector('.kanban-col-count');
        if (countEl) countEl.textContent = visible;
      });
    });
  }

  // =========================================================================
  // 8. Task Card status change – visual feedback while form submits
  // =========================================================================
  function initStatusChangeFeedback() {
    document.querySelectorAll('.card-status-select').forEach(function (select) {
      select.addEventListener('change', function () {
        var card = select.closest('.task-card');
        if (card) {
          card.style.opacity = '0.6';
          card.style.pointerEvents = 'none';
        }
      });
    });

    // Status radio buttons on task detail
    document.querySelectorAll('.status-options input[type="radio"]').forEach(function (radio) {
      radio.addEventListener('change', function () {
        var form = radio.closest('form');
        if (form) {
          // Short delay so the user sees the selection before submit
          setTimeout(function () { form.submit(); }, 150);
        }
      });
    });
  }

  // =========================================================================
  // 9. Confirmation dialogs – enhance native confirm() with nicer inline msg
  //    (native confirm is fine for MVP; this just gives feedback on cancel)
  // =========================================================================
  function initDeleteConfirmations() {
    // Forms with data-confirm attribute (progressive enhancement)
    document.querySelectorAll('form[data-confirm]').forEach(function (form) {
      form.addEventListener('submit', function (e) {
        var msg = form.getAttribute('data-confirm');
        if (!window.confirm(msg)) {
          e.preventDefault();
        }
      });
    });
  }

  // =========================================================================
  // 10. Smooth scroll to #comments anchor
  // =========================================================================
  function initCommentScroll() {
    if (window.location.hash === '#comments') {
      var el = document.getElementById('comments');
      if (el) {
        setTimeout(function () {
          el.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 100);
      }
    }
  }

  // =========================================================================
  // 11. Active nav link detection (extra safety beyond Django template logic)
  // =========================================================================
  function initActiveNavLinks() {
    var path  = window.location.pathname;
    var links = document.querySelectorAll('.nav-link');
    links.forEach(function (link) {
      var href = link.getAttribute('href');
      if (href && href !== '/' && path.startsWith(href)) {
        link.classList.add('active');
      }
    });
  }

  // =========================================================================
  // 12. Navbar scroll shadow
  // =========================================================================
  function initNavbarScroll() {
    var navbar = document.getElementById('navbar');
    if (!navbar) return;
    window.addEventListener('scroll', function () {
      if (window.scrollY > 4) {
        navbar.style.boxShadow = '0 2px 12px rgb(0 0 0 / 0.08)';
      } else {
        navbar.style.boxShadow = '';
      }
    }, { passive: true });
  }

  // =========================================================================
  // 13. Project description character counter on create/edit forms
  // =========================================================================
  function initProjectFormEnhancements() {
    var descArea  = document.querySelector('textarea[name="description"]');
    var helpEl    = document.getElementById('descCount');
    if (!descArea || !helpEl) return;

    var MAX_DESC = 2000;
    function updateCount() {
      var remaining = MAX_DESC - descArea.value.length;
      helpEl.textContent = remaining >= 0
        ? remaining + ' characters remaining'
        : 'Description is too long';
      helpEl.style.color = remaining < 50 ? 'var(--clr-danger)' : '';
    }
    descArea.addEventListener('input', updateCount);
    updateCount();
  }

  // =========================================================================
  // 14. Table row click – make entire project-list rows clickable
  // =========================================================================
  function initTableRowLinks() {
    document.querySelectorAll('.data-table tbody tr').forEach(function (row) {
      var primaryLink = row.querySelector('.table-link');
      if (!primaryLink) return;

      row.style.cursor = 'pointer';
      row.addEventListener('click', function (e) {
        // Don't fire if user clicked an actual link/button
        if (e.target.closest('a, button, form, select')) return;
        window.location.href = primaryLink.href;
      });
    });
  }

  // =========================================================================
  // 15. Tooltip: show title attrs as styled tooltip on data-* elements
  //     (lightweight, no library)
  // =========================================================================
  function initTooltips() {
    var tooltip = document.createElement('div');
    tooltip.id = 'pf-tooltip';
    tooltip.style.cssText = [
      'position:fixed',
      'background:#1e293b',
      'color:#fff',
      'font-size:0.75rem',
      'padding:4px 10px',
      'border-radius:4px',
      'pointer-events:none',
      'opacity:0',
      'transition:opacity 0.15s',
      'z-index:9999',
      'max-width:240px',
      'white-space:nowrap',
    ].join(';');
    document.body.appendChild(tooltip);

    // Elements with a title attribute inside card footers and detail lists
    var selectors = '.task-card [title], .detail-list [title], .card-due-date[title]';
    document.querySelectorAll(selectors).forEach(function (el) {
      var originalTitle = el.getAttribute('title');
      if (!originalTitle) return;

      // Remove native browser tooltip to avoid double tooltip
      el.removeAttribute('title');
      el.setAttribute('data-tooltip', originalTitle);

      el.addEventListener('mouseenter', function (e) {
        tooltip.textContent = originalTitle;
        tooltip.style.opacity = '1';
        positionTooltip(e);
      });
      el.addEventListener('mousemove', positionTooltip);
      el.addEventListener('mouseleave', function () {
        tooltip.style.opacity = '0';
      });
    });

    function positionTooltip(e) {
      var x = e.clientX + 12;
      var y = e.clientY - 28;
      // Keep within viewport
      if (x + 240 > window.innerWidth) x = e.clientX - 250;
      if (y < 0) y = e.clientY + 12;
      tooltip.style.left = x + 'px';
      tooltip.style.top  = y + 'px';
    }
  }

  // =========================================================================
  // 16. Member role select – auto-submit with confirmation
  // =========================================================================
  function initRoleSelect() {
    document.querySelectorAll('select[name="role"]').forEach(function (select) {
      var originalValue = select.value;
      select.addEventListener('change', function () {
        var newRole = select.options[select.selectedIndex].text;
        if (window.confirm('Change role to ' + newRole + '?')) {
          select.form.submit();
        } else {
          select.value = originalValue;
        }
      });
      // Prevent double-change via onchange attr in template
      select.removeAttribute('onchange');
    });
  }

  // =========================================================================
  // Init all modules
  // =========================================================================
  ready(function () {
    initNavigation();
    initUserDropdown();
    initMessages();
    initCharCounters();
    initFormFeedback();
    initBoardSearch();
    initStatusChangeFeedback();
    initDeleteConfirmations();
    initCommentScroll();
    initActiveNavLinks();
    initNavbarScroll();
    initProjectFormEnhancements();
    initTableRowLinks();
    initTooltips();
    initRoleSelect();
  });

})();
