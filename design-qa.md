---
published: false
---
# Guide directory design QA

final result: passed

## Reference and scope

The user requested a synthesis, rather than a pixel-for-pixel clone: retain the guides' folder hierarchy and combine it with execmap's numbered sections, amber selection rail, muted text and surface hover states.

Source visual truth:
- `/Users/zaryob/Desktop/Screenshot 2026-11-08 at 00.52.34.png` — 712 × 948 px, closed topic folders.
- `/Users/zaryob/Desktop/Screenshot 2026-11-08 at 00.53.21.png` — 568 × 1256 px, execmap article navigation.

The reference crops have different content and capture density. Their spacing and hierarchy were compared as visual references, not claimed as identical viewport states. Both references and the new 340 × 780 sidebar capture were opened together in the same comparison tool result. No raster resampling was applied.

## Browser evidence

Evidence directory: `/Users/zaryob/Development/qqq/_audit/2026-11-08/guides-tree/`.
- `desktop.png`: 1280 × 720 px, default viewport, Turkish LVM article, current Linux folder open, dark theme.
- `tree.png`: focused sidebar crop, 340 × 645 px, same final state.
- `medium.png`: 900 × 900 px, 280 px sidebar, complete folder list, dark theme.
- `mobile.png`: 390 × 844 px, directory expanded above the Docker article, bounded scrolling.
- `light.png`: 1280 × 900 px, light theme, LVM article and directory.

Captured images use one output pixel per CSS pixel. The full-page context and focused sidebar were inspected; mobile and medium screenshots were inspected separately for responsive behavior.

## Findings and iteration history

- Initial medium-width inspection: the old 250 px sidebar left too little room for wrapped document titles, and the inherited sticky offset introduced excess space above the directory. Expanded the medium sidebar to 280 px, reduced branch indentation, and changed its sticky offset to 88 px. The final 900 × 900 capture shows all folder labels and selected document text inside the sidebar; document width equals viewport width.
- Opening Linux exposed a pre-existing directory matching error: archived Linux URLs were included because the template matched substrings. Changed matching to an exact URL prefix. Both Turkish and English Linux folders now list README and the two active guides only.
- No actionable P0/P1/P2 findings remain in the requested scope.

## Required visual surfaces

- Typography: existing IBM Plex Mono, 14 px topic/document text and smaller muted section numbers. Long titles wrap without truncation.
- Layout: compact folder rows, consistent numbering/icon/label alignment, indented branch rail and full-width document selection. Archive remains separated by a rule.
- Tokens: existing paper, surface, line, ink, muted and accent variables; dark and light themes visually checked.
- Assets: existing Font Awesome folder, open-folder and document sprites, and existing suite guides/chevron sprites. No new raster assets or icon library introduced.
- Content: original guide titles, paths and locale separation retained. About and contribution links now both mark their current page in either locale.

## Validation

- Native details controls open with click and Enter; selected folder opens on article load.
- Clicking a different guide navigates and updates `aria-current="page"`.
- Mobile directory collapses automatically and can be expanded; expanded links scroll within the directory.
- English article navigation and directory titles checked.
- Browser error-log check returned no entries.
- Jekyll build succeeded; site checker passed 113 HTML pages, 4067 local links and 31 redirects.
- `git diff --check` passed.

## Implementation checklist

All requested design and navigation checks completed. No remaining required fixes.

## User revision — unnumbered sections

The user's latest instruction replaces the numbered design: remove all directory numbering and make Kılavuzlar and Arşiv independent peer headings. The archive now contains its README and Linux / image-processing folders. Both sections use native details, and the mobile initializer handles both sections.

Updated evidence: `sections-desktop.png`, `sections-mobile.png` in the same evidence directory. Checked independent section toggles, archive folder opening and current-page highlighting, and the mobile collapsed state. No remaining P0/P1/P2 findings in the requested revision.

## User revision — open-section underline and heading alignment

Open section summaries now use the accent border; closed summaries retain the neutral line. Root summary start padding is zero, placing its icon and label 10 CSS px left of the folder row alignment. Mobile open-section borders use the same accent token.

Browser checks: desktop open border `rgb(226, 181, 111)`, closed border `rgb(54, 62, 73)`; icon x positions 24 and 34 px. At 390 × 844, the open border remains amber, the alignment difference is 10 px, and there is no horizontal overflow. Evidence: `heading-line-desktop.png` (890 × 795), `heading-line-tree.png` (280 × 640 crop). Visually inspected both states and the final sidebar. No actionable P0/P1/P2 findings; final result: passed.

## User revision — single closed-section divider

Closed sections suppress the next section's top border (and the metadata top border), retaining a single neutral underline. Mobile summaries retain that same single underline. Browser checks confirmed a 1 px underline and 0 px following border for closed Guides; closed Archive also suppresses the metadata border. Reopening Archive preserves its amber underline. Screenshot: `single-divider.png` (280 × 520 crop). Build succeeded; no remaining visual findings in this change.
