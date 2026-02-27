"""
Pure-Python HTML assembler.

Takes the list of slide HTML fragments produced by the recursive agent tree
and wraps them in a complete, navigable HTML presentation page.

Features:
  - CSS scroll-snap for slide-by-slide navigation
  - Keyboard shortcuts (←→, Space, Home/End, number keys)
  - Dot navigation + prev/next buttons
  - Progress bar
  - Touch/swipe support
  - Slide number indicator
  - Fullscreen toggle (F key)
"""

from __future__ import annotations

from typing import List

from .models import PresentationBrief, SlideSpec

# ─── Templates ────────────────────────────────────────────────────────────────

_HTML = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <style>
    /* ── Reset & variables ───────────────────────────────────────────── */
    *, *::before, *::after {{ margin:0; padding:0; box-sizing:border-box; }}
    :root {{
      --c-primary:   {primary};
      --c-secondary: {secondary};
      --c-bg:        {bg};
      --c-text:      {text};
      --c-accent:    {accent};
      --font:        {font};
    }}

    /* ── Base ────────────────────────────────────────────────────────── */
    html, body {{
      width: 100%; height: 100%;
      overflow: hidden;
      background: var(--c-bg);
      color: var(--c-text);
      font-family: var(--font);
    }}

    /* ── Deck (scroll container) ─────────────────────────────────────── */
    #deck {{
      width: 100vw; height: 100vh;
      overflow-y: scroll;
      scroll-snap-type: y mandatory;
      scrollbar-width: none;
      -ms-overflow-style: none;
    }}
    #deck::-webkit-scrollbar {{ display: none; }}

    /* ── Individual slide ────────────────────────────────────────────── */
    .slide {{
      width: 100vw; height: 100vh;
      scroll-snap-align: start;
      position: relative;
      overflow: hidden;
      background: var(--c-bg);
    }}

    /* ── Progress bar (top) ──────────────────────────────────────────── */
    #progress {{
      position: fixed; top: 0; left: 0; z-index: 900;
      height: 3px;
      background: linear-gradient(90deg, var(--c-primary), var(--c-accent));
      transition: width .35s ease;
      pointer-events: none;
    }}

    /* ── Navigation buttons ──────────────────────────────────────────── */
    #nav {{
      position: fixed; bottom: 28px; right: 28px; z-index: 900;
      display: flex; gap: 10px;
    }}
    .nav-btn {{
      width: 38px; height: 38px;
      border-radius: 50%; border: none;
      background: var(--c-primary);
      color: #fff;
      font-size: 18px; line-height: 1;
      cursor: pointer;
      display: flex; align-items: center; justify-content: center;
      opacity: .75; transition: opacity .2s, transform .15s;
      box-shadow: 0 2px 12px rgba(0,0,0,.4);
    }}
    .nav-btn:hover {{ opacity: 1; transform: scale(1.1); }}

    /* ── Dot indicator ───────────────────────────────────────────────── */
    #dots {{
      position: fixed; bottom: 34px; left: 50%; transform: translateX(-50%);
      z-index: 900;
      display: flex; gap: 7px; align-items: center;
    }}
    .dot {{
      width: 7px; height: 7px; border-radius: 50%;
      background: var(--c-text); opacity: .25;
      cursor: pointer; transition: all .25s;
    }}
    .dot.active {{
      opacity: 1; background: var(--c-primary);
      transform: scale(1.4);
    }}

    /* ── Slide counter ───────────────────────────────────────────────── */
    #counter {{
      position: fixed; bottom: 32px; left: 28px; z-index: 900;
      font-size: 12px; opacity: .35; letter-spacing: .05em;
      color: var(--c-text); font-family: var(--font);
      pointer-events: none;
    }}

    /* ── Fullscreen hint ─────────────────────────────────────────────── */
    #fullscreen-hint {{
      position: fixed; top: 16px; right: 16px; z-index: 900;
      font-size: 11px; opacity: .3; color: var(--c-text);
      font-family: var(--font); pointer-events: none;
    }}
  </style>
</head>
<body>

  <!-- Progress bar -->
  <div id="progress" style="width:0"></div>

  <!-- Slide deck -->
  <div id="deck">
{slides_html}
  </div>

  <!-- Navigation -->
  <div id="nav">
    <button class="nav-btn" id="btnPrev" title="Previous (←)">&#8249;</button>
    <button class="nav-btn" id="btnNext" title="Next (→)">&#8250;</button>
  </div>

  <!-- Dots -->
  <div id="dots">
{dots_html}
  </div>

  <!-- Counter -->
  <div id="counter">1 / {total}</div>

  <!-- Fullscreen hint -->
  <div id="fullscreen-hint">Press F for fullscreen</div>

  <script>
  (function () {{
    'use strict';
    const deck    = document.getElementById('deck');
    const slides  = Array.from(document.querySelectorAll('.slide'));
    const dots    = Array.from(document.querySelectorAll('.dot'));
    const counter = document.getElementById('counter');
    const progress= document.getElementById('progress');
    const btnNext = document.getElementById('btnNext');
    const btnPrev = document.getElementById('btnPrev');
    let current   = 0;
    let isScrolling = false;

    function updateUI() {{
      const n = slides.length;
      counter.textContent = (current + 1) + ' / ' + n;
      progress.style.width = ((current + 1) / n * 100) + '%';
      dots.forEach((d, i) => d.classList.toggle('active', i === current));
    }}

    function goTo(n) {{
      if (isScrolling) return;
      current = Math.max(0, Math.min(slides.length - 1, n));
      isScrolling = true;
      slides[current].scrollIntoView({{ behavior: 'smooth', block: 'start' }});
      updateUI();
      setTimeout(() => {{ isScrolling = false; }}, 600);
    }}

    btnNext.addEventListener('click', () => goTo(current + 1));
    btnPrev.addEventListener('click', () => goTo(current - 1));
    dots.forEach((d, i) => d.addEventListener('click', () => goTo(i)));

    document.addEventListener('keydown', e => {{
      if (['ArrowRight','ArrowDown',' '].includes(e.key)) {{ e.preventDefault(); goTo(current + 1); }}
      if (['ArrowLeft','ArrowUp'].includes(e.key))        {{ e.preventDefault(); goTo(current - 1); }}
      if (e.key === 'Home') goTo(0);
      if (e.key === 'End')  goTo(slides.length - 1);
      if (e.key === 'f' || e.key === 'F') {{
        if (!document.fullscreenElement) document.documentElement.requestFullscreen();
        else document.exitFullscreen();
      }}
      const num = parseInt(e.key);
      if (!isNaN(num) && num >= 1 && num <= slides.length) goTo(num - 1);
    }});

    /* Sync dot on manual scroll */
    let scrollTimer;
    deck.addEventListener('scroll', () => {{
      clearTimeout(scrollTimer);
      scrollTimer = setTimeout(() => {{
        const idx = Math.round(deck.scrollTop / deck.clientHeight);
        if (idx !== current) {{ current = idx; updateUI(); }}
      }}, 80);
    }});

    /* Touch / swipe */
    let touchStartY = 0;
    deck.addEventListener('touchstart', e => {{ touchStartY = e.touches[0].clientY; }}, {{passive:true}});
    deck.addEventListener('touchend', e => {{
      const dy = touchStartY - e.changedTouches[0].clientY;
      if (Math.abs(dy) > 40) goTo(current + (dy > 0 ? 1 : -1));
    }}, {{passive:true}});

    updateUI();
  }})();
  </script>
</body>
</html>
"""

_SLIDE = """\
    <section class="slide" id="slide-{index}" aria-label="{title}">
      {content}
    </section>"""

_DOT = '    <div class="dot" data-index="{index}" title="{title}"></div>'


# ─── Public API ────────────────────────────────────────────────────────────────

def assemble_presentation(
    brief: PresentationBrief,
    slides: List[SlideSpec],
    contents: List[str],
) -> str:
    """
    Assemble the final HTML presentation from slide fragments.

    Parameters
    ----------
    brief:
        The original presentation brief (provides title + style).
    slides:
        Ordered list of SlideSpec objects (provides metadata for each slide).
    contents:
        Ordered list of HTML strings, one per slide, as produced by the
        recursive agent tree.
    """
    s = brief.style

    slides_html = "\n".join(
        _SLIDE.format(
            index=slide.index,
            title=_esc(slide.title),
            content=content,
        )
        for slide, content in zip(slides, contents)
    )

    dots_html = "\n".join(
        _DOT.format(index=slide.index, title=_esc(slide.title))
        for slide in slides
    )

    return _HTML.format(
        title=_esc(brief.title),
        primary=s.primary_color,
        secondary=s.secondary_color,
        bg=s.background_color,
        text=s.text_color,
        accent=s.accent_color,
        font=s.font_family,
        slides_html=slides_html,
        dots_html=dots_html,
        total=len(slides),
    )


def _esc(text: str) -> str:
    """Minimal HTML attribute escaping."""
    return text.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;")
