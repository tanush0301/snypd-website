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
  // 7. HIGGSFIELD 3D MOUSE PARALLAX & TILT ENGINE
  // ==========================================================================
  const stage = document.getElementById('hero3dStage');
  const cardLeft = document.getElementById('cardLeft');
  const cardRight = document.getElementById('cardRight');

  if (stage && cardLeft && cardRight && window.innerWidth > 1200) {
    let mouseX = 0;
    let mouseY = 0;
    let targetLeftX = 0;
    let targetLeftY = 0;
    let targetRightX = 0;
    let targetRightY = 0;

    let currentLeftX = 0;
    let currentLeftY = 0;
    let currentRightX = 0;
    let currentRightY = 0;

    window.addEventListener('mousemove', (e) => {
      const { innerWidth, innerHeight } = window;
      const normX = (e.clientX / innerWidth) * 2 - 1; // -1 to 1
      const normY = (e.clientY / innerHeight) * 2 - 1; // -1 to 1

      // Left card tilt parameters
      targetLeftX = normY * -16 + 4;  // rotateX
      targetLeftY = normX * 22 + 12; // rotateY

      // Right card tilt parameters
      targetRightX = normY * -16 + 4; // rotateX
      targetRightY = normX * 22 - 12; // rotateY
    });

    // High-FPS Smooth Inertia Loop
    function render3DParallax() {
      // Lerp damping
      currentLeftX += (targetLeftX - currentLeftX) * 0.08;
      currentLeftY += (targetLeftY - currentLeftY) * 0.08;
      currentRightX += (targetRightX - currentRightX) * 0.08;
      currentRightY += (targetRightY - currentRightY) * 0.08;

      cardLeft.style.transform = `rotateX(${currentLeftX.toFixed(2)}deg) rotateY(${currentLeftY.toFixed(2)}deg) translateZ(40px)`;
      cardRight.style.transform = `rotateX(${currentRightX.toFixed(2)}deg) rotateY(${currentRightY.toFixed(2)}deg) translateZ(40px)`;

      requestAnimationFrame(render3DParallax);
    }

    render3DParallax();
  }

});

