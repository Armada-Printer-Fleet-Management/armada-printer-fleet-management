// Renders the shared sidebar into <nav> on every page.
//
// Add a page here and it appears in the navigation everywhere. The list is
// inline rather than fetched, because pages are opened directly from disk and
// fetch() is blocked on file:// URLs.

const SECTIONS = [
  {
    title: "Start here",
    links: [
      { href: "index.html", text: "Documentation home" },
      { href: "git-hygiene.html", text: "Git hygiene" },
    ],
  },
  {
    title: "Applications",
    links: [{ href: "desktop.html", text: "Desktop application" }],
  },
  {
    title: "Reference",
    links: [
      { href: "../AGENTS.md", text: "Agent instructions" },
      { href: "../.integrity/POLICY.md", text: "AI use policy" },
    ],
  },
];

function render() {
  const nav = document.querySelector("nav");
  if (!nav) return;

  // Pages may sit in subdirectories, so links resolve relative to docs/.
  const depth = (document.body.dataset.depth || "0") | 0;
  const prefix = "../".repeat(depth);
  const here = window.location.pathname.split("/").pop() || "index.html";

  const parts = ['<div class="brand">Capstone docs</div>'];

  for (const section of SECTIONS) {
    parts.push(`<h2>${section.title}</h2>`);
    for (const link of section.links) {
      const current = link.href === here ? ' aria-current="page"' : "";
      parts.push(`<a href="${prefix}${link.href}"${current}>${link.text}</a>`);
    }
  }

  nav.innerHTML = parts.join("");
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", render);
} else {
  render();
}
