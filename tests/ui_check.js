// Browser check for tests/test_ui_browser.py (SYNTHETIC data served on loopback; nothing leaves the machine).
// Usage: node tests/ui_check.js BASE_URL PLAYWRIGHT_MODULE CHROMIUM_PATH [SCREENSHOT_DIR]
// Prints one JSON object with what it observed; the Python test makes the assertions.
"use strict";
const [BASE, MODULE, CHROME, SHOTS] = process.argv.slice(2);
const { chromium } = require(MODULE);

(async () => {
  const out = { posts: [], external: [], errors: [], checks: {} };
  const browser = await chromium.launch({
    executablePath: CHROME,
    args: ["--disable-background-networking", "--disable-component-update", "--no-pings", "--disable-domain-reliability"],
  });
  async function page(w, h) {
    const ctx = await browser.newContext({ viewport: { width: w, height: h } });
    const p = await ctx.newPage();
    // every request that is not to the local test server is aborted and recorded
    await p.route("**/*", (route) => (route.request().url().startsWith(BASE) ? route.continue() : (out.external.push(route.request().url()), route.abort())));
    p.on("pageerror", (e) => out.errors.push(String(e)));
    p.on("request", (r) => { if (r.method() === "POST") out.posts.push(r.url().replace(BASE, "")); });
    return p;
  }
  const overflow = (p) => p.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  const text = (p) => p.evaluate(() => document.body.innerText);
  const banned = /open decisions|suggested interpretation|unread here|claude is paused|only smelling can decide|how should .* be expressed/i;

  for (const [w, h, tag] of [[1440, 900, "desktop"], [390, 844, "mobile"]]) {
    const p = await page(w, h);
    await p.goto(BASE + "/"); await p.waitForSelector("#brand");
    out.checks[tag + "_start_overflow"] = await overflow(p);
    if (SHOTS) await p.screenshot({ path: `${SHOTS}/home-${tag}.png`, fullPage: true });
    await p.context().close();
  }

  const p = await page(1440, 900);
  await p.goto(BASE + "/"); await p.waitForSelector("#brand");
  const brandPicks = await p.$$eval('[aria-label="Try"] button', (b) => b.map((x) => x.textContent));
  const contextPicks = await p.$$eval('[aria-label="For example"] button', (b) => b.map((x) => [x.textContent, x.dataset.value]));
  out.checks.brand_picks = brandPicks;
  out.checks.context_picks = contextPicks;
  out.checks.context_label = await p.textContent('label[for="intent"]');
  out.checks.context_placeholder = await p.getAttribute("#intent", "placeholder");
  out.checks.context_hint = await p.textContent("#intent-hint");
  // quick picks fill the fields and send nothing
  await p.click('[aria-label="Try"] button:has-text("Comme des Garçons")');
  out.checks.brand_after_pick = await p.inputValue("#brand");
  out.checks.brand_pick_pressed = await p.getAttribute('[aria-label="Try"] button:has-text("Comme des Garçons")', "aria-pressed");
  await p.click('[aria-label="For example"] button:has-text("Hotel lobby")');
  out.checks.context_after_pick = await p.inputValue("#intent");
  await p.click("#intent"); await p.keyboard.press("End"); await p.keyboard.type(" in Istanbul");
  out.checks.context_after_edit = await p.inputValue("#intent");
  out.checks.context_pick_pressed_after_edit = await p.getAttribute('[aria-label="For example"] button:has-text("Hotel lobby")', "aria-pressed");
  out.checks.posts_after_picks = out.posts.length;
  // free text in both fields, then the one research request
  await p.fill("#brand", "Synthbrand");
  await p.fill("#intent", "A scent for a private gallery opening");
  await p.click('button[type="submit"]');
  await p.waitForSelector(".res .lead .kicker, .stage .options", { timeout: 20000 });
  if (await p.$(".stage .options")) {
    await p.click(".option button");
    await p.waitForSelector(".res .lead .kicker", { timeout: 20000 });
  }
  await p.waitForTimeout(300);
  const resultText = await text(p);
  out.checks.result_banned = (resultText.match(banned) || [null])[0];
  out.checks.result_has_suggest_block = !!(await p.$("#suggest"));
  out.checks.result_sections = await p.$$eval(".sec > h2", (hs) => hs.map((x) => x.textContent));
  out.checks.result_context_line = await p.textContent(".intentline").catch(() => null);
  out.checks.desktop_result_overflow = await overflow(p);
  if (SHOTS) await p.screenshot({ path: `${SHOTS}/result-desktop.png`, fullPage: true });
  const id = await p.evaluate(() => location.hash.split("/").pop());
  out.checks.posts_after_result = out.posts.slice();

  const m = await page(390, 844);
  await m.goto(BASE + "/#/s/" + id); await m.waitForSelector(".lead .kicker");
  out.checks.mobile_result_overflow = await overflow(m);
  if (SHOTS) await m.screenshot({ path: `${SHOTS}/result-mobile.png`, fullPage: true });

  const pr = await page(1000, 1400);
  await pr.goto(BASE + "/brief/" + id); await pr.waitForSelector(".grid"); await pr.waitForTimeout(800);
  const pdfText = await text(pr);
  out.checks.pdf_banned = (pdfText.match(banned) || [null])[0];
  out.checks.pdf_sections = await pr.$$eval(".grid h2", (hs) => hs.map((x) => x.textContent));
  await pr.emulateMedia({ media: "print" });
  const pdf = await pr.pdf({ format: "A4", printBackground: true, preferCSSPageSize: true, path: SHOTS ? `${SHOTS}/brief.pdf` : undefined });
  out.checks.pdf_pages = (pdf.toString("latin1").match(/\/Type\s*\/Page[^s]/g) || []).length;
  out.checks.posts_after_pdf = out.posts.slice();
  await browser.close();
  console.log(JSON.stringify(out));
})().catch((e) => { console.log(JSON.stringify({ fatal: String(e) })); process.exit(1); });
