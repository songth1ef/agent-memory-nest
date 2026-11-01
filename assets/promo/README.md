# Promo cards

A 9-card carousel (1080×1440, 3:4) for social posts, in a minimal light
Liquid Glass style: near-white background with soft diagonal light streaks,
two-tone large titles, and glass capsule tags.

| File | What it is |
|---|---|
| `template.html` | The look: background, type scale, spacing, glass chips. Open it in a browser to see the cover. |
| `build.py` | Fills the template with each card's text and exports PNGs with headless Chrome. |
| `slides/01.png` … `09.png` | The rendered cards. |
| `cover.png` | Card 1, for quick previews. |

## Regenerate

```bash
python3 assets/promo/build.py            # macOS with Google Chrome installed
python3 assets/promo/build.py --chrome /path/to/chrome
```

Edit the text in `SLIDES` inside `build.py`; change the look in `template.html`.

## Rules the layout depends on

- Type follows iOS: SF Pro for Latin and digits, PingFang SC for Chinese
  (`-apple-system, system-ui` first in the font stack). On a machine without
  these fonts the cards will render, but will not look the same.
- Sizes are set for phone viewing (a 1080-px card shows at about 375 pt):
  title 128 px, body 46 px, tags 38 px.
- Spacing is on an 8-px grid: 96 px page margins; 28 / 56 / 72 / 88 px between
  kicker, title, body, tags and footer.
- Keep the strong title line to about six Chinese characters and each body line
  to about 18, or they wrap.
