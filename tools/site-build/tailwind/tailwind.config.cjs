// Tailwind 3.4.17 build for umbrasec.dev. The site used the Play CDN script
// (default config, no theme changes), which compiled classes in the browser.
// This is the same default config compiled once, ahead of time, into
// assets/tailwind.css. Rebuild with: npm run build:css
// `build_indexes.py --check` and CI fail if the committed CSS is stale.
//
// content lists every served file that can carry a class name: the pages and
// the scripts that build markup at runtime. A class used only in a new kind of
// file must have that file added here, or it ships without styles.
module.exports = {
  content: [
    "./*.html",
    "./guide/*.html",
    "./research/*.html",
    "./tools/*.html",
    "./tools/sigma-pack/*.html",
    "./assets/*.js",
    "./functions/**/*.js",
  ],
};
