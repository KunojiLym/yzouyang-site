# Boot CLS review context (not generated)

- **Systems / credentials tablet pane (~56px):** layout-shift sources pointed at the index row snapping from `0.38fr/0.62fr` and a wrong SSR-first panel before hash boot — not the reading-context bar (it stays `display:none` on those routes). Fix: SSR-visible first index panel for no-JS, `html.js` hides extras, per-panel `yzLibraryRevealPanel`, pre-paint hash panel switch in `THEME_BOOT_SCRIPT` + `LIBRARY_HASH_BOOT_SCRIPT` (no `38dvh` grid override).
- **Notes (~36px):** reading-context bar without reserved slot on collapsed index; late index collapse. Fix: single notes-only `.library-reading-context[hidden]` reserve during boot, synchronous `is-index-collapsed` on wide hash boot, SSR expanded index (`html:not(.js)`).
