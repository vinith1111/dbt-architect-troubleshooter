import assert from "node:assert/strict";
import { chromium } from "playwright";
import { fileURLToPath } from "node:url";
import path from "node:path";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const pageUrl = "file://" + path.join(root, "docs", "index.html");
const browser = await chromium.launch({ headless: true });
const errors = [];

try {
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  page.on("pageerror", error => errors.push(error.message));
  await page.goto(pageUrl);
  // The learning and guided tools are intentionally collapsed by default.
  await page.locator("details.more-learning > summary").click();
  await page.getByRole("heading", { name: /Real project dbt problems ni practice cheddam/i }).waitFor();

  const cases = [
    { value: "duplicates", correctIndex: 1 },
    { value: "test", correctIndex: 1 },
    { value: "slow", correctIndex: 1 },
    { value: "missing", correctIndex: 0 },
    { value: "schema", correctIndex: 0 }
  ];

  for (const item of cases) {
    await page.locator("#scenario-select").selectOption(item.value);
    const options = page.locator('input[name="scenario-choice"]');
    assert.equal(await options.count(), 3, `${item.value}: expected 3 answer options`);
    await options.nth(item.correctIndex).check();
    await page.locator("#scenario-check").click();
    await page.locator("#scenario-feedback").waitFor({ state: "visible" });
    assert.match(await page.locator("#scenario-feedback-title").innerText(), /Good first check/i, `${item.value}: expected correct-answer feedback`);
    assert.equal(await page.locator("#scenario-next li").count(), 4, `${item.value}: expected 4 next checks`);
    assert.ok((await page.locator("#scenario-validate").innerText()).length > 10);
    assert.ok((await page.locator("#scenario-prevent").innerText()).length > 10);
    await page.locator("#scenario-reset").click();
    assert.equal(await page.locator("#scenario-feedback").isVisible(), false, `${item.value}: feedback should reset`);
    assert.equal(await page.locator('input[name="scenario-choice"]:checked').count(), 0, `${item.value}: selection should reset`);
  }

  // The wizard must handle an unknown problem without inventing a diagnosis.
  await page.locator("#guided-problem").selectOption("unknown");
  await page.getByRole("button", { name: /Problem details prepare cheyyi/i }).click();
  assert.match(await page.locator("#result-title").innerText(), /Problem ni kalisi narrow down cheddam/i);
  assert.match(await page.locator("#diagnosis").innerText(), /Problem jarigindani ardham ayyindi/i);

  // A known symptom should route to its matching deterministic guidance.
  await page.locator("#guided-problem").selectOption("duplicate");
  await page.getByRole("button", { name: /Problem details prepare cheyyi/i }).click();
  assert.match(await page.locator("#result-title").innerText(), /Duplicate rows observed/i);

  // Check narrow mobile layout for horizontal overflow.
  await page.setViewportSize({ width: 375, height: 812 });
  await page.reload();
  const dimensions = await page.evaluate(() => ({
    viewport: document.documentElement.clientWidth,
    content: document.documentElement.scrollWidth
  }));
  assert.ok(dimensions.content <= dimensions.viewport, `mobile horizontal overflow: ${JSON.stringify(dimensions)}`);
  assert.deepEqual(errors, [], `browser JavaScript errors: ${errors.join("; ")}`);

  console.log("Browser smoke tests passed: 5 scenarios, feedback/reset, guided unknown/known routing, mobile overflow, and no uncaught JS errors.");
} finally {
  await browser.close();
}
