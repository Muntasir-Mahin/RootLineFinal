(() => {
  'use strict';
  const root = document.documentElement;
  root.classList.add('js');
  const toastBox = document.getElementById('site-toast');
  let toastTimer;
  function toast(message) {
    clearTimeout(toastTimer);
    toastBox.textContent = message;
    toastBox.hidden = false;
    toastTimer = setTimeout(() => { toastBox.hidden = true; }, 6000);
  }
  const dialog = document.getElementById('confirm-dialog');
  let confirming = false;
  function confirmAction(message) {
    if (!dialog?.showModal) return Promise.resolve(window.confirm(message));
    if (confirming) return Promise.resolve(false);
    confirming = true;
    document.getElementById('confirm-description').textContent = message;
    dialog.returnValue = 'cancel';
    const previous = document.activeElement;
    return new Promise(resolve => {
      dialog.addEventListener('close', () => {
        confirming = false;
        previous?.focus();
        resolve(dialog.returnValue === 'confirm');
      }, {once: true});
      dialog.showModal();
    });
  }
  window.RootLine = {toast, confirm: confirmAction};


  const menuButton = document.getElementById('menu-toggle');
  const links = document.getElementById('site-links');
  const mobile = matchMedia('(max-width: 1023px)');
  function menu(open) {
    menuButton.setAttribute('aria-expanded', String(open));
    links.classList.toggle('is-open', open);
    // Inert prevents keyboard focus entering the closed mobile menu.
    links.inert = mobile.matches && !open;

  }
  menuButton.hidden = false;
  menu(false);
  mobile.addEventListener('change', () => menu(false));
  menuButton.addEventListener('click', () => menu(menuButton.getAttribute('aria-expanded') !== 'true'));
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && mobile.matches && menuButton.getAttribute('aria-expanded') === 'true') {
      menu(false); menuButton.focus();
    }
  });
  document.addEventListener('click', event => {
    if (mobile.matches && !event.target.closest('.site-nav')) menu(false);
  });

  document.querySelectorAll('.nav-popover').forEach(popover => {
    popover.addEventListener('toggle', () => {
      if (!mobile.matches && popover.open) {
        document.querySelectorAll('.nav-popover').forEach(other => { if (other !== popover) other.open = false; });
      }
    });
  });
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && !mobile.matches) {
      document.querySelectorAll('.nav-popover[open]').forEach(item => { item.open = false; item.querySelector('summary').focus(); });
    }
  });
  document.addEventListener('click', event => {
    if (!mobile.matches && !event.target.closest('.site-nav')) document.querySelectorAll('.nav-popover').forEach(item => { item.open = false; });
  });
  const searchToggle = document.getElementById('search-toggle');
  const searchPanel = document.getElementById('header-search');
  if (searchToggle && searchPanel) {
    searchToggle.hidden = false;
    function search(open) {
      searchPanel.classList.toggle('is-open', open);
      searchToggle.setAttribute('aria-expanded', String(open));
      if (open) { menu(false); document.getElementById('site-query').focus(); }
    }
    searchToggle.addEventListener('click', () => search(searchToggle.getAttribute('aria-expanded') !== 'true'));
    document.querySelectorAll('[data-open-search]').forEach(link => link.addEventListener('click', event => {
      if (mobile.matches) { event.preventDefault(); scrollTo({top:0}); search(true); }
    }));
    document.addEventListener('keydown', event => {
      if (event.key === 'Escape' && searchPanel.classList.contains('is-open')) { search(false); searchToggle.focus(); }
    });
    menuButton.addEventListener('click', () => search(false));
  }
  document.querySelectorAll('.category-menu').forEach(item => {
    document.addEventListener('keydown', event => { if (event.key === 'Escape' && item.open) { item.open=false; item.querySelector('summary').focus(); } });
    document.addEventListener('click', event => { if (!item.contains(event.target)) item.open=false; });
  });
  const top = document.getElementById('back-to-top');
  const scrollBar = document.getElementById('scroll-progress');
  let scheduled = false;
  function scrollState() {
    const range = document.documentElement.scrollHeight - innerHeight;
    scrollBar.style.transform = `scaleX(${range > 0 ? Math.min(1, Math.max(0, scrollY / range)) : 0})`;
    top.hidden = scrollY < 400;
    scheduled = false;
  }
  addEventListener('scroll', () => {
    if (!scheduled) { scheduled = true; requestAnimationFrame(scrollState); }
  }, {passive: true});
  addEventListener('resize', scrollState);
  new ResizeObserver(scrollState).observe(document.body);
  scrollState();
  top.addEventListener('click', () => {
    scrollTo({top: 0, behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth'});
    document.getElementById('main-content').focus({preventScroll: true});
  });

  const contact = document.getElementById('contact-toggle');
  const panel = document.getElementById('contact-panel');
  let previousOverflow = '';
  const toastHome = toastBox.parentNode;
  const toastAnchor = toastBox.nextSibling;
  contact.hidden = false;
  function closeContact() { panel.close(); }
  contact.addEventListener('click', () => {
    if (panel.open) { closeContact(); return; }
    previousOverflow = document.body.style.overflow;
    panel.hidden = false;
    toastBox.hidden = true;
    panel.append(toastBox);
    panel.showModal();
    document.body.style.overflow = 'hidden';
    contact.setAttribute('aria-expanded', 'true');
    panel.querySelector('[data-contact-close]').focus();
  });
  panel.querySelector('[data-contact-close]').addEventListener('click', closeContact);
  panel.addEventListener('cancel', event => { event.preventDefault(); closeContact(); });
  panel.addEventListener('close', () => {
    panel.hidden = true;
    toastHome.insertBefore(toastBox, toastAnchor);
    document.body.style.overflow = previousOverflow;
    contact.setAttribute('aria-expanded', 'false');
    contact.focus({preventScroll:true});
  });
  panel.addEventListener('click', event => {
    const box = panel.getBoundingClientRect();
    if (event.target === panel && (event.clientX < box.left || event.clientX > box.right || event.clientY < box.top || event.clientY > box.bottom)) closeContact();
  });
  panel.addEventListener('keydown', event => {
    if (event.key !== 'Tab') return;
    const controls = [...panel.querySelectorAll('a[href],button:not([disabled]),[tabindex="0"]')].filter(el => el.getClientRects().length);
    const first = controls[0], last = controls[controls.length-1];
    if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
    else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
  });

  const consentBanner = document.getElementById('cookie-banner');
  const preferences = document.getElementById('cookie-settings');
  const consent = () => document.cookie.split('; ').find(item => item.startsWith('rootline_consent='))?.split('=')[1];
  function captureCampaign() {
    if (consent() !== 'analytics') return;
    const query = new URLSearchParams(location.search);
    const campaign = {};
    ['utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content'].forEach(key => {
      const value = query.get(key)?.trim();
      if (value) campaign[key] = value.slice(0, 150);
    });
    if (Object.keys(campaign).length) {
      try { sessionStorage.setItem('rootline-campaign', JSON.stringify(campaign)); } catch { /* Storage unavailable. */ }
      dispatchEvent(new CustomEvent('rootline:campaign', {detail: campaign}));
    }
  }
  preferences.hidden = false;
  consentBanner.hidden = ['essential', 'analytics'].includes(consent());
  preferences.addEventListener('click', () => { consentBanner.hidden = false; consentBanner.querySelector('button').focus(); });
  consentBanner.querySelectorAll('[data-consent]').forEach(button => button.addEventListener('click', () => {
    document.cookie = `rootline_consent=${button.dataset.consent}; Path=/; Max-Age=15552000; SameSite=Lax${location.protocol === 'https:' ? '; Secure' : ''}`;
    if (button.dataset.consent === 'essential') {
      try { sessionStorage.removeItem('rootline-campaign'); } catch { /* Storage unavailable. */ }
    } else captureCampaign();
    consentBanner.hidden = true;
    toast('Cookie preferences saved.');
  }));
  captureCampaign();

  document.querySelectorAll('[data-copy-link], [data-copy-contact]').forEach(button => { button.hidden = false; });
  document.addEventListener('click', async event => {
    const dismiss = event.target.closest('[data-dismiss-message]');
    if (dismiss) dismiss.closest('.site-message').remove();
    const copy = event.target.closest('[data-copy-link], [data-copy-message], [data-copy-contact]');
    if (copy) {
      const text = copy.hasAttribute('data-copy-contact') ? copy.dataset.copyContact : copy.hasAttribute('data-copy-link') ? `${location.origin}${location.pathname}` :
        copy.closest('.ask-message')?.querySelector('.ask-bubble')?.textContent;
      try {
        if (!text) throw new Error();
        await navigator.clipboard.writeText(text);
        toast(copy.hasAttribute('data-copy-contact') ? `${copy.dataset.copyLabel} copied.` : copy.hasAttribute('data-copy-link') ? 'Link copied.' : 'Answer copied.');
      } catch { toast('Copy is unavailable in this browser. Select the text or address and copy it manually.'); }
    }
    const link = event.target.closest('a[href]');
    if (!link || event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey || link.target || link.hasAttribute('download')) return;
    const target = new URL(link.href, location.href);
    if (target.origin === location.origin && ['http:', 'https:'].includes(target.protocol) &&
        (target.pathname !== location.pathname || target.search !== location.search)) {
      root.classList.add('is-navigating');
    }
  });

  // Ask for confirmation before native destructive forms; keep the clicked
  // submitter so alternate actions, names, and values reach the server intact.
  const approved = new WeakSet();
  document.addEventListener('submit', async event => {
    const form = event.target;
    if (event.defaultPrevented || form.closest('dialog')) return;
    if (form.dataset.confirm && !approved.has(form)) {
      event.preventDefault();
      const submitter = event.submitter;
      if (await confirmAction(form.dataset.confirm)) {
        approved.add(form);
        form.requestSubmit(submitter || undefined);
        approved.delete(form);
      }
      return;
    }
    if (form.method.toLowerCase() !== 'post') return;
    if (form.dataset.submitting === 'true') { event.preventDefault(); return; }
    form.dataset.submitting = 'true';
    form.setAttribute('aria-busy', 'true');
    // Do not disable successful controls: their names and values must be posted.
    form.querySelectorAll('button[type=submit], input[type=submit]').forEach(button => button.setAttribute('aria-disabled', 'true'));
    const status = document.createElement('p');
    status.className = 'form-progress';
    status.setAttribute('role', 'status');
    status.textContent = 'Submitting… Please wait.';
    form.append(status);
  });
  addEventListener('pageshow', () => {
    root.classList.remove('is-navigating');
    document.querySelectorAll('[data-submitting]').forEach(form => {
      delete form.dataset.submitting;
      form.removeAttribute('aria-busy');
      form.querySelectorAll('[aria-disabled]').forEach(button => button.removeAttribute('aria-disabled'));
      form.querySelector('.form-progress')?.remove();
    });
  });
})();
