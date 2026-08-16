//  Visual regression gate (HANDOFF-PHASE4 §2.2) — thresholds live here so a
//  change to them is a reviewable diff, not a magic number buried in a spec.
//
//  maxDiffPixelRatio: fraction of pixels allowed to differ from baseline
//  before the spec fails. 2% absorbs font-AA drift between OS font stacks
//  (Windows baselines vs ubuntu CI) without hiding a real visual change —
//  the adversarial-test bar is "a deliberate visual change gets flagged",
//  and any deliberate change moves far more than 2% of pixels.
export const visualGate = {
    maxDiffPixelRatio: 0.02,
    //  pixelmatch: anti-aliased pixels are detected and skipped, not counted
    //  as diffs (includeAA: false). pixelDiff threshold is per-pixel color
    //  distance; 0.1 is the pixelmatch default.
    pixelThreshold: 0.1,
};
