/* ==========================================================================
   SNYPD STANDALONE INTERACTIVE ENGINE (main.js)
   Combines Navbar, Hero Live Feed, Engine 3D Board, Real Examples, Pricing & FAQ
   ========================================================================== */

document.addEventListener("DOMContentLoaded", function() {

  // Mobile navbar toggle lives in the "DEFECT 3" + "FINAL POLISH" IIFEs
  // further down this file -- do not re-add a duplicate handler here, it
  // was previously bound three times across this file and index.html's
  // inline script, and relied on an accidental even-count cancellation to
  // appear to work at all.

  // Footer copyright year -- was hardcoded and had already drifted 2 years
  // stale (2024) before this fix. Self-updating so it can't happen again.
  const copyYearEl = document.getElementById('copyYear');
  if (copyYearEl) {
    copyYearEl.textContent = new Date().getFullYear();
  }

  // ==========================================================================
  // 2. HERO DASHBOARD MOCKUP LIVE FEED SIMULATION -- REMOVED 2026-09-20
  // --------------------------------------------------------------------------
  // This drove #feed-container inside index.html's .app-window, a mockup of a
  // dashboard SNYPD no longer has (left sidebar, a StockX nav item). Both the
  // mockup and this simulation are gone; the hero now renders the real
  // topbar-based dashboard in "The Intercept" component, whose own camera
  // engine is self-contained in index.html next to its markup.
  //
  // Worth recording why this had to go rather than be repointed: the five
  // listings here were invented, and every row it inserted carried the
  // hardcoded date literal "04 July 2026" with a live clock time appended --
  // a fabricated timestamp on the highest-traffic page on the site. The
  // replacement uses six real catches read out of public.current_ads.
  // ==========================================================================

  // ==========================================================================
  // 3. THE ENGINE 3D BOARD TILT PHYSICS
  // ==========================================================================
  const boardWrapper = document.getElementById('boardWrapper');
  const vsBoard = document.getElementById('vsBoard');
  const isMobile = () => window.innerWidth <= 1024;

  if (boardWrapper && vsBoard) {
    boardWrapper.addEventListener('mousemove', (e) => {
      if (isMobile()) return;
      const rect = boardWrapper.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      
      const xPct = (x / rect.width - 0.5) * 2;
      const yPct = (y / rect.height - 0.5) * 2;
      
      const maxRot = 5;
      const rY = xPct * maxRot;
      const rX = yPct * maxRot * -1;
      
      vsBoard.style.setProperty('--rX', `${rX}deg`);
      vsBoard.style.setProperty('--rY', `${rY}deg`);
    });

    boardWrapper.addEventListener('mouseleave', () => {
      if (isMobile()) return;
      vsBoard.style.setProperty('--rX', '0deg');
      vsBoard.style.setProperty('--rY', '0deg');
    });

    vsBoard.addEventListener('mousemove', (e) => {
      const rect = vsBoard.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      vsBoard.style.setProperty('--mouse-x', `${x}px`);
      vsBoard.style.setProperty('--mouse-y', `${y}px`);
    });
  }

  // ==========================================================================
  // 4. REAL EXAMPLES INTERACTIVE GALLERY SYSTEM
  // ==========================================================================
  const queueList = document.getElementById('queueList');
  const focusStage = document.getElementById('focusStage');
  const loader = document.getElementById('stageLoader');
  
  if (queueList && focusStage) {
    const galleryData = [
      { id: 0, img: '/assets/img/6a49f591f2b3031b92a87da3_1783074655.webp', title: "Supreme 99 Football Top Black", price: "€ 120,00", market: "Est: €200+", size: "L", cond: "Very Good", time: "Just now", source: "search", label: "Example" },
      { id: 1, img: '/assets/img/6a49f4c0a4873ec61828a489_1783146176.jpeg', title: "Jordan 4 Bred OG", price: "€ 140,00", market: "Est: €300+", size: "42", cond: "Very Good", time: "1m ago", source: "catalog", label: "Example" },
      { id: 2, img: '/assets/img/6a4e03733184f099d185451d_jordan-1-travis-scott-velvet.jpg', title: "Air Jordan 1 Low Travis Scott Velvet Brown", price: "€ 225,00", market: "Est: €750+", size: "42.5", cond: "Very Good", time: "5m ago", source: "catalog", label: "Example" },
      { id: 3, img: '/assets/img/6a49f4c0088ffb1e4478ccba_1772617611.png', title: "Jordan 1 High \"Mocha\"", price: "€ 84,00", market: "Est: €400+", size: "43", cond: "Good", time: "12m ago", source: "catalog", label: "Example" },
      { id: 4, img: '/assets/img/6a49f4c0e0c8a747768678bb_1783110478.jpg', title: "Yeezy Slide Onyx", price: "€ 23,00", market: "Est: €90+", size: "42", cond: "Brand New", time: "20m ago", source: "catalog", label: "Example" }
    ];

    let activeId = 0;
    const fImage = document.getElementById('fImage');
    const fTitle = document.getElementById('fTitle');
    const fPrice = document.getElementById('fPrice');
    const fSize = document.getElementById('fSize');
    const fCond = document.getElementById('fCond');
    const fTime = document.getElementById('fTime');
    const fSource = document.getElementById('fSource');

    function renderQueue() {
      queueList.innerHTML = '';
      galleryData.forEach(item => {
        if (item.id === activeId) return;

        const card = document.createElement('div');
        card.className = 'queue-card';
        card.innerHTML = `
          <div class="qc-thumb" style="background-image: url('${item.img}');"></div>
          <div class="qc-content">
            <div class="qc-top"><span class="qc-label">${item.label}</span></div>
            <h4 class="qc-title">${item.title}</h4>
            <div class="qc-meta">${item.size} · ${item.cond} · ${item.price} · ${item.time}</div>
          </div>
        `;
        
        card.addEventListener('click', () => swapItem(item.id));
        queueList.appendChild(card);
      });
    }

    function swapItem(newId) {
      if (activeId === newId) return;
      activeId = newId;

      if (loader) loader.classList.add('active');
      renderQueue();

      setTimeout(() => {
        const data = galleryData.find(i => i.id === activeId);
        if (fImage) fImage.style.backgroundImage = `url('${data.img}')`;
        if (fTitle) fTitle.textContent = data.title;
        if (fPrice) fPrice.innerHTML = `${data.price} <span class="market">${data.market}</span>`;
        if (fSize) fSize.textContent = data.size;
        if (fCond) fCond.textContent = data.cond;
        if (fTime) fTime.textContent = data.time;
        if (fSource) fSource.textContent = data.source;

        if (loader) loader.classList.remove('active');
      }, 600);
    }

    renderQueue();

    focusStage.addEventListener('mousemove', (e) => {
      if (isMobile()) return;
      const rect = focusStage.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      const xPct = (x / rect.width - 0.5) * 2;
      const yPct = (y / rect.height - 0.5) * 2;
      focusStage.style.setProperty('--mx', xPct);
      focusStage.style.setProperty('--my', yPct);
    });

    focusStage.addEventListener('mouseleave', () => {
      if (isMobile()) return;
      focusStage.style.setProperty('--mx', '0');
      focusStage.style.setProperty('--my', '0');
    });
  }

  // ==========================================================================
  // 5. PRICING & SUPABASE PLAN INTEGRATION
  // ==========================================================================
  const pricingRoot = document.querySelector(".snypd-pricing");
  if (pricingRoot) {
    const signupUrl = "/signup";
    const fallbackManageUrl = "https://whop.com/@me/settings/orders/";
    const activeStatuses = ["active", "trialing", "past_due", "unpaid"];
    const planLabels = { free: "FREE", kickstart: "KICKSTART", pro: "PRO", elite: "ELITE" };

    const banner = pricingRoot.querySelector("[data-current-plan-banner]");
    const bannerText = pricingRoot.querySelector("[data-current-plan-text]");
    const manageLink = pricingRoot.querySelector("[data-manage-link]");
    const cards = Array.from(pricingRoot.querySelectorAll("[data-plan-card]"));
    const ctas = Array.from(pricingRoot.querySelectorAll("[data-whop-link]"));

    const authState = { isLoggedIn: false, currentPlan: null, status: null, manageUrl: fallbackManageUrl };

    function normalizePlan(plan) {
      const value = String(plan || "").trim().toLowerCase();
      if (value === "starter" || value === "kickoff") return "kickstart";
      if (["kickstart", "pro", "elite", "free"].includes(value)) return value;
      return null;
    }

    function isActiveStatus(status) {
      return activeStatuses.includes(String(status || "").trim().toLowerCase());
    }

    function setCurrentPlan(plan, manageUrl, status) {
      const normalizedPlan = normalizePlan(plan) || "free";
      const active = normalizedPlan === "free" || isActiveStatus(status);
      if (!active) return;

      authState.currentPlan = normalizedPlan;
      authState.status = status || null;
      authState.manageUrl = manageUrl || fallbackManageUrl;

      cards.forEach(card => {
        card.classList.toggle("is-current", card.getAttribute("data-plan-card") === normalizedPlan);
      });

      if (banner && bannerText) {
        bannerText.textContent = planLabels[normalizedPlan] || normalizedPlan.toUpperCase();
        banner.classList.add("is-visible");
      }

      if (manageLink) {
        manageLink.href = authState.manageUrl;
        manageLink.classList.toggle("is-visible", normalizedPlan !== "free");
      }

      ctas.forEach(cta => {
        const ctaPlan = normalizePlan(cta.getAttribute("data-plan"));
        const whopUrl = cta.getAttribute("data-whop-link");
        cta.removeAttribute("aria-disabled");

        if (ctaPlan === normalizedPlan) {
          if (normalizedPlan === "free") {
            cta.textContent = "Current plan";
            cta.setAttribute("aria-disabled", "true");
            cta.removeAttribute("href");
          } else {
            cta.textContent = "Manage subscription";
            cta.href = authState.manageUrl;
          }
          return;
        }

        if (ctaPlan === "free") cta.textContent = "Start free";
        if (ctaPlan === "kickstart") cta.textContent = "Start Kickstart";
        if (ctaPlan === "pro") cta.textContent = "Start Pro";
        if (ctaPlan === "elite") cta.textContent = "Start Elite";
        if (whopUrl) cta.href = whopUrl;
      });
    }

    function getSupabaseClient() {
      return window.SNYPD && window.SNYPD.supabase ? window.SNYPD.supabase : null;
    }

    async function loadUserPlan() {
      const supabase = getSupabaseClient();
      if (!supabase || !supabase.auth || !supabase.auth.getSession) return;

      try {
        const sessionResponse = await supabase.auth.getSession();
        const session = sessionResponse && sessionResponse.data ? sessionResponse.data.session : null;
        const user = session && session.user ? session.user : null;
        if (!user) return;

        authState.isLoggedIn = true;
        if (!supabase.from) return;

        const profileResponse = await supabase
          .from("users")
          .select("subscription_plan, sub_status, whop_manage_url")
          .eq("id", user.id)
          .maybeSingle();

        const profile = profileResponse && profileResponse.data ? profileResponse.data : null;
        if (profile) {
          setCurrentPlan(profile.subscription_plan || "free", profile.whop_manage_url, profile.sub_status);
        } else {
          setCurrentPlan("free", null, "active");
        }
      } catch (error) {
        authState.isLoggedIn = false;
      }
    }

    ctas.forEach(cta => {
      cta.addEventListener("click", function(event) {
        if (cta.getAttribute("aria-disabled") === "true") {
          event.preventDefault();
          return;
        }
        if (!authState.isLoggedIn) {
          event.preventDefault();
          window.location.href = signupUrl;
          return;
        }
        const href = cta.getAttribute("href") || cta.getAttribute("data-whop-link");
        if (!href || href === "https://whop.com/checkout/plan_jPBUwsY7FaO3w") {
          event.preventDefault();
          window.location.href = signupUrl;
          return;
        }

        const ctaPlan = normalizePlan(cta.getAttribute("data-plan"));

        // Own current paid plan's button reads "Manage subscription" here -
        // send that to Whop's real account page. No documented embedded
        // billing-portal exists, only checkout for a NEW plan.
        if (ctaPlan === authState.currentPlan) return;

        const overlay = pricingRoot.querySelector(`[data-whop-embed-overlay="${ctaPlan}"]`);
        if (overlay) {
          event.preventDefault();
          overlay.hidden = false;
        }
      });
    });

    document.querySelectorAll("[data-whop-embed-close]").forEach(btn => {
      btn.addEventListener("click", () => {
        btn.closest("[data-whop-embed-overlay]").hidden = true;
      });
    });

    document.querySelectorAll("[data-whop-embed-overlay]").forEach(overlay => {
      overlay.addEventListener("click", event => {
        if (event.target === overlay) overlay.hidden = true;
      });
    });

    // Fires when the embedded checkout completes (data-whop-checkout-on-complete).
    // The webhook that updates Supabase runs async on Whop's side, so this
    // sends the buyer to the dashboard rather than trying to re-render the
    // plan state immediately - the dashboard's own load already re-checks it.
    window.snypdCheckoutComplete = function () {
      document.querySelectorAll("[data-whop-embed-overlay]").forEach(overlay => {
        overlay.hidden = true;
      });
      window.location.href = "/dashboard";
    };

    loadUserPlan();
  }

  // ==========================================================================
  // 6. FAQ ACCORDION LOGIC
  // ==========================================================================
  document.querySelectorAll('.faq-question').forEach(button => {
    button.addEventListener('click', () => {
      const faqItem = button.parentElement;
      const isActive = faqItem.classList.contains('active');
      if (isActive) {
        faqItem.classList.remove('active');
      } else {
        faqItem.classList.add('active');
      }
    });
  });

  // ==========================================================================
  // 7 & 8 (canvas frame-scrubbing engine, Lenis smooth scroll, chapter-dot
  // nav, snipe search/filter demo) -- REMOVED 2026-08-24. All of it targeted
  // #storyTrack/#storyCanvas/.story-chapter-dots/#snipeSearchInput/
  // .vault-card-mini, which belonged to the video-hero story track pulled on
  // 2026-08-23 (see CLAUDE.md). None of those elements exist in the current
  // page, so every function here was a guarded no-op -- except the Lenis
  // instance, which had no such guard: it was replacing native scroll
  // physics site-wide for a feature that no longer exists. Removed rather
  // than left running.
  // ==========================================================================

  // ==========================================================================
  // 9. GSAP SCROLL REVEALS FOR POST-HERO SECTIONS -- REMOVED 2026-08-24
  // ==========================================================================
  // This animated the dashboard mockup and set .ultra-section/#proofSection/
  // #pricing/.faq-section to opacity:0 until a Lenis+ScrollTrigger reveal
  // fired on scroll. It never ran on this site before main.js was wired into
  // index.html for the (now-removed) video hero -- confirmed the pre-redesign
  // index.html never loaded main.js at all, so pricing/FAQ/etc. were always
  // just plain visible content. The reveal stopped completing reliably
  // (reported live: pricing and the FAQ section not showing), most likely a
  // Lenis/ScrollTrigger scroll-position sync issue that gets worse the
  // further a section sits from the top of the page -- exactly matching
  // which sections broke. Removed rather than debugged further: nothing here
  // could be visually re-verified in this environment, and every section
  // this touched is real content that must always be visible, not a nice-to-
  // have animation worth that risk. Do not re-add without a live, human-
  // confirmed check that the reveal actually completes on a real scroll.

});




/* ================================================================
   SNYPD DEFECT 3 — MOBILE NAVBAR TOGGLE (CUSTOM ISLAND NAV)
   ================================================================ */
(function () {
  function initSnypdCustomMobileNav() {
    var toggleBtn = document.getElementById('snypdMobileToggle');
    var mobileMenu = document.getElementById('snypdMobileMenu');

    if (!toggleBtn) toggleBtn = document.querySelector('.snypd-island__mobile-btn');
    if (!mobileMenu) mobileMenu = document.querySelector('.snypd-mobile-menu');

    if (!toggleBtn || !mobileMenu) return;

    if (toggleBtn.getAttribute('data-snypd-nav-bound') === '1') return;
    toggleBtn.setAttribute('data-snypd-nav-bound', '1');

    toggleBtn.addEventListener('click', function (e) {
      e.preventDefault();
      e.stopPropagation();
      
      var isActive = mobileMenu.classList.contains('active');
      
      if (isActive) {
        mobileMenu.classList.remove('active');
        toggleBtn.setAttribute('aria-expanded', 'false');
        mobileMenu.setAttribute('aria-hidden', 'true');
      } else {
        mobileMenu.classList.add('active');
        toggleBtn.setAttribute('aria-expanded', 'true');
        mobileMenu.removeAttribute('aria-hidden');
      }
    });

    var menuLinks = mobileMenu.querySelectorAll('a');
    menuLinks.forEach(function (link) {
      link.addEventListener('click', function () {
        mobileMenu.classList.remove('active');
        toggleBtn.setAttribute('aria-expanded', 'false');
        mobileMenu.setAttribute('aria-hidden', 'true');
      });
    });

    document.addEventListener('click', function (e) {
      if (!mobileMenu.contains(e.target) && !toggleBtn.contains(e.target)) {
        if (mobileMenu.classList.contains('active')) {
          mobileMenu.classList.remove('active');
          toggleBtn.setAttribute('aria-expanded', 'false');
          mobileMenu.setAttribute('aria-hidden', 'true');
        }
      }
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initSnypdCustomMobileNav);
  } else {
    initSnypdCustomMobileNav();
  }
})();

/* ================================================================
   SNYPD FINAL POLISH — NAV STATE GUARDS
   ================================================================ */
(function () {
  function initSnypdFinalNavGuards() {
    var menu = document.getElementById('snypdMobileMenu') || document.querySelector('.snypd-mobile-menu');
    var toggle = document.getElementById('snypdMobileToggle') || document.querySelector('.snypd-island__mobile-btn');

    if (!menu || !toggle) {
      return;
    }

    function closeMenu() {
      menu.classList.remove('active');
      toggle.setAttribute('aria-expanded', 'false');
      menu.setAttribute('aria-hidden', 'true');
    }

    window.addEventListener('resize', function () {
      if (window.innerWidth > 991 && menu.classList.contains('active')) {
        closeMenu();
      }
    });

    document.addEventListener('keydown', function (event) {
      if (event.key === 'Escape' && menu.classList.contains('active')) {
        closeMenu();
      }
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initSnypdFinalNavGuards);
  } else {
    initSnypdFinalNavGuards();
  }
})();
