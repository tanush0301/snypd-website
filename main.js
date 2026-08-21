/* ==========================================================================
   SNYPD STANDALONE INTERACTIVE ENGINE (main.js)
   Combines Navbar, Hero Live Feed, Engine 3D Board, Real Examples, Pricing & FAQ
   ========================================================================== */

document.addEventListener("DOMContentLoaded", function() {
  
  // ==========================================================================
  // 1. FLOATING ISLAND NAVBAR & MOBILE TOGGLE
  // ==========================================================================
  const toggleBtn = document.getElementById("snypdMobileToggle");
  const mobileMenu = document.getElementById("snypdMobileMenu");
  const menuLinks = document.querySelectorAll(".mobile-menu-link");

  if (toggleBtn && mobileMenu) {
    toggleBtn.addEventListener("click", function(e) {
      e.stopPropagation();
      mobileMenu.classList.toggle("active");
    });

    document.addEventListener("click", function(e) {
      if (!mobileMenu.contains(e.target) && e.target !== toggleBtn) {
        mobileMenu.classList.remove("active");
      }
    });

    menuLinks.forEach(link => {
      link.addEventListener("click", () => {
        mobileMenu.classList.remove("active");
      });
    });
  }

  // ==========================================================================
  // 2. HERO DASHBOARD MOCKUP LIVE FEED SIMULATION
  // ==========================================================================
  const feedContainer = document.getElementById('feed-container');
  if (feedContainer) {
    const sampleData = [
      { img: '/assets/img/6a49f591f2b3031b92a87da3_1783074655.webp', name: 'Supreme 99 Football Top Black', meta: 'Supreme • L • Very Good • search', price: '€ 120,00' },
      { img: '/assets/img/6a49f4c0a4873ec61828a489_1783146176.jpeg', name: 'Jordan 4 Bred OG', meta: 'Jordan • 42 • Very Good • catalog', price: '€ 140,00' },
      { img: '/assets/img/6a4e03733184f099d185451d_jordan-1-travis-scott-velvet.jpg', name: 'Air Jordan 1 Low Travis Scott Velvet Brown', meta: 'Jordan • 42.5 • Very Good • catalog', price: '€ 225,00' },
      { img: '/assets/img/6a49f4c0088ffb1e4478ccba_1772617611.png', name: 'Jordan 1 High "Mocha"', meta: 'Jordan • 43 • Good • catalog', price: '€ 84,00' },
      { img: '/assets/img/6a49f4c0e0c8a747768678bb_1783110478.jpg', name: 'Yeezy Slide Onyx', meta: 'Yeezy • 42 • Brand New • catalog', price: '€ 23,00' }
    ];

    let dataIndex = 1;

    function createFeedRow(item) {
      const div = document.createElement('div');
      div.className = 'feed-item';
      div.style.opacity = '0';
      div.style.transform = 'translateY(-10px)';
      
      const uploadTime = new Date().toLocaleTimeString('en-US', { hour12: false });

      div.innerHTML = `
        <div class="feed-img" style="background-image:url('${item.img}')"></div>
        <div class="feed-info">
          <div class="feed-title-row">
            <div class="feed-title">${item.name}</div>
            <div class="feed-price">${item.price}</div>
          </div>
          <div class="feed-meta">${item.meta} • Uploaded on Vinted at 04 July 2026 at ${uploadTime}</div>
        </div>
        <a href="/signup" class="feed-action">
          Snype
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="5" y1="12" x2="19" y2="12"></line><polyline points="12 5 19 12 12 19"></polyline></svg>
        </a>
      `;
      return div;
    }

    setInterval(() => {
      const item = sampleData[dataIndex % sampleData.length];
      const newRow = createFeedRow(item);
      
      feedContainer.insertBefore(newRow, feedContainer.firstChild);
      
      setTimeout(() => {
        newRow.style.transition = 'all 0.4s var(--ease-fluid)';
        newRow.style.opacity = '1';
        newRow.style.transform = 'translateY(0)';
      }, 50);

      const rows = feedContainer.querySelectorAll('.feed-item');
      if (rows.length > 3) {
        rows[rows.length - 1].remove();
      }

      dataIndex++;
    }, 3500);
  }

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
      { id: 0, img: '/assets/img/6a49f591f2b3031b92a87da3_1783074655.webp', title: "Supreme 99 Football Top Black", price: "€ 120,00", market: "Est: €200+", size: "L", cond: "Very Good", time: "Just now", source: "search", label: "Primary Slot" },
      { id: 1, img: '/assets/img/6a49f4c0a4873ec61828a489_1783146176.jpeg', title: "Jordan 4 Bred OG", price: "€ 140,00", market: "Est: €300+", size: "42", cond: "Very Good", time: "1m ago", source: "catalog", label: "Example Slot" },
      { id: 2, img: '/assets/img/6a4e03733184f099d185451d_jordan-1-travis-scott-velvet.jpg', title: "Air Jordan 1 Low Travis Scott Velvet Brown", price: "€ 225,00", market: "Est: €750+", size: "42.5", cond: "Very Good", time: "5m ago", source: "catalog", label: "Example Slot" },
      { id: 3, img: '/assets/img/6a49f4c0088ffb1e4478ccba_1772617611.png', title: "Jordan 1 High \"Mocha\"", price: "€ 84,00", market: "Est: €400+", size: "43", cond: "Good", time: "12m ago", source: "catalog", label: "Example Slot" },
      { id: 4, img: '/assets/img/6a49f4c0e0c8a747768678bb_1783110478.jpg', title: "Yeezy Slide Onyx", price: "€ 23,00", market: "Est: €90+", size: "42", cond: "Brand New", time: "20m ago", source: "catalog", label: "Example Slot" }
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
        }
      });
    });

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
  // 7. APPLE-STANDARD 60FPS CANVAS FRAME SCRUBBING ENGINE
  // ==========================================================================
  const track = document.getElementById('storyTrack');
  const canvas = document.getElementById('storyCanvas');
  const ctx = canvas ? canvas.getContext('2d') : null;
  const progressBar = document.getElementById('storyProgressBar');
  const chapterDots = document.querySelectorAll('.story-chapter-dots .dot');
  const chapters = [
    document.getElementById('chapter1'),
    document.getElementById('chapter2'),
    document.getElementById('chapter3'),
    document.getElementById('chapter4')
  ];

  // Initialize Lenis Luxury Smooth Scrolling
  let lenis = null;
  if (typeof Lenis !== 'undefined') {
    lenis = new Lenis({
      duration: 1.2,
      easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)), // Exponential smooth decay
      orientation: 'vertical',
      gestureOrientation: 'vertical',
      smoothWheel: true,
      wheelMultiplier: 1.0,
      touchMultiplier: 1.8,
      infinite: false
    });

    function rafLenis(time) {
      lenis.raf(time);
      requestAnimationFrame(rafLenis);
    }
    requestAnimationFrame(rafLenis);

    if (typeof ScrollTrigger !== 'undefined') {
      lenis.on('scroll', ScrollTrigger.update);
    }
  }

  // Preload 80 High-Res 3D Obsidian Sphere Frames
  const frameCount = 80;
  const frameImages = [];
  let currentRenderedFrame = 0;
  let targetFrameIndex = 0;
  let smoothFrameIndex = 0;

  for (let i = 0; i < frameCount; i++) {
    const img = new Image();
    const padIndex = String(i).padStart(3, '0');
    img.src = `/assets/frames/frame_${padIndex}.jpg`;
    img.onload = () => {
      if (i === 0 && ctx) {
        drawCanvasFrame(0);
      }
    };
    frameImages.push(img);
  }

  function drawCanvasFrame(idx) {
    if (!ctx || !canvas || !frameImages[idx]) return;
    const img = frameImages[idx];
    if (img.complete && img.naturalWidth > 0) {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
      currentRenderedFrame = idx;
    }
  }

  function onScrollProgress(progress) {
    // Exact target frame index
    targetFrameIndex = Math.min(Math.max(progress * (frameCount - 1), 0), frameCount - 1);
  }

  // 60FPS High-Precision Lerp Frame Drawing Loop
  function renderCanvasScrubLoop() {
    // Lerp with 0.25 damping factor for organic fluid response
    smoothFrameIndex += (targetFrameIndex - smoothFrameIndex) * 0.25;
    const rounded = Math.round(smoothFrameIndex);
    if (rounded !== currentRenderedFrame) {
      drawCanvasFrame(rounded);
    }
    requestAnimationFrame(renderCanvasScrubLoop);
  }
  requestAnimationFrame(renderCanvasScrubLoop);

  function computeScroll() {
    if (!track) return;
    const rect = track.getBoundingClientRect();
    const totalScrollable = track.offsetHeight - window.innerHeight;
    if (totalScrollable <= 0) return;
    const progress = Math.min(Math.max(-rect.top / totalScrollable, 0), 1);
    onScrollProgress(progress);
  }

  if (lenis) {
    lenis.on('scroll', computeScroll);
  } else {
    window.addEventListener('scroll', computeScroll, { passive: true });
  }

  // Click on Dots to Jump to Chapter smoothly with Lenis
  chapterDots.forEach((dot) => {
    dot.addEventListener('click', () => {
      const step = parseInt(dot.getAttribute('data-step') || '1', 10);
      if (!track) return;
      const totalScrollable = track.offsetHeight - window.innerHeight;
      const stepProgress = (step - 1) / 3.0; // 0, 0.33, 0.66, 1.0
      const targetScroll = track.offsetTop + (stepProgress * totalScrollable);
      
      if (lenis) {
        lenis.scrollTo(targetScroll, { duration: 1.4 });
      } else {
        window.scrollTo({ top: targetScroll, behavior: 'smooth' });
      }
    });
  });

  // ==========================================================================
  // 8. SEARCH & FILTER INTERACTION IN CHAPTER 2
  // ==========================================================================
  const searchInput = document.getElementById('snipeSearchInput');
  const snipeBtn = document.getElementById('snipeSimulateBtn');
  const filterPills = document.querySelectorAll('.filter-pill');
  const vaultCards = document.querySelectorAll('.vault-card-mini');

  function filterMiniVault(query) {
    const q = query.trim().toLowerCase();
    vaultCards.forEach(card => {
      const tags = (card.getAttribute('data-tags') || '').toLowerCase();
      const title = (card.querySelector('strong')?.textContent || '').toLowerCase();
      if (q === '' || q === 'all' || tags.includes(q) || title.includes(q)) {
        card.style.display = 'flex';
        card.style.opacity = '1';
      } else {
        card.style.opacity = '0.2';
        setTimeout(() => {
          if (card.style.opacity === '0.2') card.style.display = 'none';
        }, 200);
      }
    });
  }

  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      filterMiniVault(e.target.value);
      filterPills.forEach(p => p.classList.remove('active'));
    });
  }

  if (snipeBtn) {
    snipeBtn.addEventListener('click', () => {
      snipeBtn.innerHTML = '<span>⚡ Scanning...</span>';
      setTimeout(() => {
        snipeBtn.innerHTML = '<span>Snyped!</span><kbd>0.018s</kbd>';
        setTimeout(() => {
          snipeBtn.innerHTML = '<span>Snype Scan</span><kbd>⚡ 18ms</kbd>';
        }, 2000);
      }, 300);
    });
  }

  filterPills.forEach(pill => {
    pill.addEventListener('click', () => {
      filterPills.forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      const query = pill.getAttribute('data-query') || '';
      if (searchInput) {
        searchInput.value = query === 'all' ? '' : query;
      }
      filterMiniVault(query);
    });
  });

  // ==========================================================================
  // 9. GSAP SCROLL REVEALS FOR POST-HERO SECTIONS
  // ==========================================================================
  if (typeof gsap !== 'undefined' && typeof ScrollTrigger !== 'undefined') {
    gsap.registerPlugin(ScrollTrigger);

    // App Window Reveal
    const appWindow = document.querySelector('.app-window');
    if (appWindow) {
      gsap.from(appWindow, {
        scrollTrigger: {
          trigger: '.app-reveal-wrapper',
          start: 'top 85%',
          end: 'top 30%',
          scrub: 1
        },
        scale: 0.88,
        y: 60,
        opacity: 0.5,
        ease: 'power2.out'
      });
    }

    // Other Sections
    const sections = document.querySelectorAll('.ultra-section, #proofSection, #features, #pricing, .faq-section');
    sections.forEach(sec => {
      gsap.from(sec.children, {
        scrollTrigger: {
          trigger: sec,
          start: 'top 80%'
        },
        y: 40,
        opacity: 0,
        stagger: 0.12,
        duration: 0.8,
        ease: 'power3.out'
      });
    });
  }

});



