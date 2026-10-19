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

  // The learning roadmap should be visible and subjects should be in a beginner-friendly order.
  const roadmapLinks = page.locator(".roadmap-grid a");
  assert.equal(await roadmapLinks.count(), 7, "expected five core learning steps plus two interview labs");
  const roadmapTitles = await roadmapLinks.locator("strong").allTextContents();
  assert.deepEqual(roadmapTitles, [
    "SQL Foundations",
    "Python Basics",
    "Snowflake",
    "dbt Projects",
    "AWS for Data Engineering",
    "Interview Readiness Lab",
    "Snowflake Interview Lab"
  ]);

  // Every subject lesson should offer the same cross-course navigation.
  const coursePages = [
    { file: "sql-learn.html", active: "SQL" },
    { file: "python-learn.html", active: "Python" },
    { file: "snowflake-learn.html", active: "Snowflake" },
    { file: "learn.html", active: "dbt" },
    { file: "aws-learn.html", active: "AWS" }
  ];
  for (const course of coursePages) {
    await page.goto("file://" + path.join(root, "docs", course.file));
    assert.equal(await page.locator(".course-path a").count(), 5, `${course.file}: expected all course links`);
    assert.equal(await page.locator(".course-path a[aria-current='page']").innerText(), course.active);
  }

  await page.goto(pageUrl);
  // The learning and guided tools are intentionally collapsed by default.
  await page.locator("details.more-learning > summary").click();
  await page.getByRole("heading", { name: /Practice real-world dbt problems/i }).waitFor();

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
  await page.locator("#problem").fill("An unusual dbt behavior that does not match any known rule");
  await page.getByRole("button", { name: /Diagnose problem/i }).click();
  assert.match(await page.locator("#result-title").innerText(), /Let's narrow down the problem together/i);
  assert.match(await page.locator("#diagnosis").textContent(), /The problem is clear/i);

  // A known symptom should route to its matching deterministic guidance.
  await page.locator("#guided-problem").selectOption("duplicate");
  await page.locator("#problem").fill("Duplicate rows in an incremental dbt model");
  await page.getByRole("button", { name: /Diagnose problem/i }).click();
  assert.match(await page.locator("#result-title").innerText(), /Duplicate rows in an incremental model/i);

  // Check narrow mobile layout for horizontal overflow.
  await page.setViewportSize({ width: 375, height: 812 });
  await page.reload();
  const dimensions = await page.evaluate(() => ({
    viewport: document.documentElement.clientWidth,
    content: document.documentElement.scrollWidth
  }));
  assert.ok(dimensions.content <= dimensions.viewport, `mobile horizontal overflow: ${JSON.stringify(dimensions)}`);
  assert.deepEqual(errors, [], `browser JavaScript errors: ${errors.join("; ")}`);

  // Verify that the learning page makes difficult concepts concrete in both languages.
  await page.setViewportSize({ width: 1280, height: 900 });
  await page.goto("file://" + path.join(root, "docs", "learn.html"));
  await page.getByRole("heading", { name: "What Is dbt?" }).waitFor();
  assert.match(await page.locator(".learning-guide").innerText(), /Mental model/i);
  assert.equal(await page.locator(".learning-guide ol li").count(), 3);

  await page.getByRole("button", { name: /Incremental models & unique_key/ }).click();
  assert.match(await page.locator(".learning-guide").innerText(), /growing ledger/i);
  assert.equal(await page.locator(".learning-guide ol li").count(), 3);
  await page.locator('[data-language="tinglish"]').click();
  assert.match(await page.locator(".learning-guide").innerText(), /Simple ga imagine chey/i);
  assert.match(await page.locator(".learning-guide").innerText(), /Incremental model growing ledger/i);

  await page.setViewportSize({ width: 375, height: 812 });
  const learnDimensions = await page.evaluate(() => ({
    viewport: document.documentElement.clientWidth,
    content: document.documentElement.scrollWidth
  }));
  assert.ok(learnDimensions.content <= learnDimensions.viewport, `learning page mobile overflow: ${JSON.stringify(learnDimensions)}`);
  assert.deepEqual(errors, [], `browser JavaScript errors: ${errors.join("; ")}`);

  // Verify the new cross-course interview lab: all ten cases render, answers open,
  // language switching works, and self-ratings update the score.
  await page.setViewportSize({ width: 1280, height: 900 });
  await page.goto("file://" + path.join(root, "docs", "interview-readiness.html"));
  assert.equal(await page.locator("article.card").count(), 10, "expected 10 cross-course interview cases");
  await page.locator('[data-answer="0"]').click();
  assert.equal(await page.locator("#a0").evaluate(el => el.classList.contains("open")), true);
  await page.locator('[data-lang="tg"]').click();
  await page.locator('[data-answer="0"]').click();
  assert.match(await page.locator("#a0").innerText(), /Munduga input grain/i);
  await page.locator('input[name="rating0"][value="2"]').check();
  assert.match(await page.locator("#score").innerText(), /2 \/ 20/);
  await page.setViewportSize({ width: 375, height: 812 });
  const interviewDimensions = await page.evaluate(() => ({
    viewport: document.documentElement.clientWidth,
    content: document.documentElement.scrollWidth
  }));
  assert.ok(interviewDimensions.content <= interviewDimensions.viewport, `interview lab mobile overflow: ${JSON.stringify(interviewDimensions)}`);

  // Verify the Snowflake lab navigation, case rendering, rating UI and mobile layout.
  await page.setViewportSize({ width: 1280, height: 900 });
  await page.goto("file://" + path.join(root, "docs", "snowflake-interview-readiness.html"));
  assert.equal(await page.locator("#nav button").count(), 14, "expected 14 Snowflake interview cases");
  const firstCaseTitle = await page.locator("#case h2").innerText();
  await page.locator("#nav button").nth(1).click();
  assert.notEqual(await page.locator("#case h2").innerText(), firstCaseTitle, "case navigation should change the active case");
  assert.equal(await page.locator("#case .rating input").count(), 4, "each Snowflake case should have four self-rating options");
  await page.locator("#case .rating input").last().check();
  assert.match(await page.locator("#score").innerText(), /3 \/ 42/);
  await page.setViewportSize({ width: 375, height: 812 });
  const snowflakeInterviewDimensions = await page.evaluate(() => ({
    viewport: document.documentElement.clientWidth,
    content: document.documentElement.scrollWidth
  }));
  assert.ok(snowflakeInterviewDimensions.content <= snowflakeInterviewDimensions.viewport, `Snowflake interview lab mobile overflow: ${JSON.stringify(snowflakeInterviewDimensions)}`);
  assert.deepEqual(errors, [], `browser JavaScript errors: ${errors.join("; ")}`);

  console.log("Browser smoke tests passed: course navigation, diagnostic scenarios, English/Tinglish, both interview labs, scoring, mobile overflow, and no uncaught JS errors.");
} finally {
  await browser.close();
}
