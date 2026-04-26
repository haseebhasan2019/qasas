// Reader: loads volume JSON and renders one PDF page at a time


const params = new URLSearchParams(window.location.search);
const volume = parseInt(params.get('v')) || 1;
let currentPageIndex = parseInt(params.get('p') || '0');

let volumeData = null;
let pages = []; // flat list of {chapterTitle, firstPageIndex, page} across all chapters

async function loadVolume() {
  try {
    const res = await fetch(`data/volume_${volume}.json`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    volumeData = await res.json();

    // Flatten all pages across chapters into one array, tracking each chapter's starting index
    pages = [];
    volumeData.chapters.forEach(ch => {
      const firstPageIndex = pages.length;
      ch.pages.forEach(page => {
        pages.push({ chapterTitle: ch.title, firstPageIndex, page });
      });
    });

    renderSidebar();
    renderPage(currentPageIndex);
  } catch (err) {
    document.getElementById('content').innerHTML =
      `<p class="loading-msg error-msg">خطأ في تحميل البيانات: ${err.message}<br>
       تأكد من تشغيل الموقع من خادم محلي وأن ملفات JSON موجودة في web/data/</p>`;
    console.error(err);
  }
}

function renderSidebar() {
  const list = document.getElementById('chapter-list');
  list.innerHTML = '';

  // Sidebar shows chapters; clicking jumps to first page of that chapter.
  // firstPageIndex is stored as a data attribute so updateSidebarActive()
  // can highlight the correct chapter without re-computing page indices.
  volumeData.chapters.forEach(ch => {
    const firstPageIndex = pages.findIndex(p => p.chapterTitle === ch.title);
    const btn = document.createElement('button');
    btn.className = 'chapter-item';
    btn.dataset.firstPage = firstPageIndex;
    btn.textContent = ch.title;
    btn.onclick = () => {
      renderPage(firstPageIndex);
      closeSidebar();
    };
    list.appendChild(btn);
  });
  updateSidebarActive();
}

function updateSidebarActive() {
  // Highlight whichever chapter's range contains the current page index
  const btns = document.querySelectorAll('.chapter-item');
  btns.forEach(btn => {
    const first = parseInt(btn.dataset.firstPage);
    const next = parseInt(btn.nextElementSibling?.dataset.firstPage ?? pages.length);
    btn.classList.toggle('active', currentPageIndex >= first && currentPageIndex < next);
  });
}

function renderPage(index) {
  if (!pages.length || index < 0 || index >= pages.length) return;

  currentPageIndex = index;
  const { chapterTitle, page } = pages[index];

  // Update URL without reload
  const url = new URL(window.location);
  url.searchParams.set('v', volume);
  url.searchParams.set('p', index);
  window.history.replaceState({}, '', url);

  // Update header title to chapter name
  document.title = `${chapterTitle} — قصص النبيين`;
  document.getElementById('chapter-title').textContent = chapterTitle;

  // Build content
  const content = document.getElementById('content');
  content.innerHTML = '';

  page.paragraphs.forEach(para => {
    const p = document.createElement('p');
    p.id = para.id;
    p.dataset.fullText = para.text;
    p.textContent = para.text;
    content.appendChild(p);
  });

  // Apply current tashkeel preference
  applyTashkeelState();

  // Scroll to top
  content.scrollTop = 0;

  // Update nav buttons and counter
  updateNav();
  updateSidebarActive();
}

function updateNav() {
  document.getElementById('prev-btn').disabled = currentPageIndex <= 0;
  document.getElementById('next-btn').disabled = currentPageIndex >= pages.length - 1;
  document.getElementById('chapter-counter').textContent =
    `${currentPageIndex + 1} / ${pages.length}`;
}

function navigate(direction) {
  renderPage(currentPageIndex + direction);
}

// Sidebar toggle
const sidebar = document.getElementById('sidebar');
const overlay = document.getElementById('overlay');

document.getElementById('menu-btn').onclick = () => {
  sidebar.classList.add('open');
  overlay.classList.add('visible');
};

document.getElementById('sidebar-close').onclick = closeSidebar;
overlay.onclick = closeSidebar;

function closeSidebar() {
  sidebar.classList.remove('open');
  overlay.classList.remove('visible');
}

// Keyboard navigation
document.addEventListener('keydown', e => {
  if (e.key === 'ArrowLeft') navigate(-1);   // RTL: left = back
  if (e.key === 'ArrowRight') navigate(1); // RTL: right = forward
});

// Start
loadVolume();
