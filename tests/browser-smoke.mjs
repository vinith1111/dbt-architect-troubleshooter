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
  assert.equal(await roadmapLinks.count(), 5, "expected five core learning steps");
  const roadmapTitles = await roadmapLinks.locator("strong").allTextContents();
  assert.deepEqual(roadmapTitles, [
    "SQL Foundations",
    "Python Basics",
    "Snowflake",
    "dbt Projects",
    "AWS for Data Engineering"
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

  // Verify every Snowflake lesson renders its production-depth sections.
  await page.setViewportSize({ width: 1280, height: 900 });
  await page.goto("file://" + path.join(root, "docs", "snowflake-learn.html"));
  const snowflakeLessons = page.locator("#navList button");
  assert.equal(await snowflakeLessons.count(), 23, "expected 23 Snowflake lessons");
  for (let i = 0; i < 23; i++) {
    await snowflakeLessons.nth(i).click();
    const lesson = page.locator("#lesson");
    await lesson.locator("h2").waitFor();
    for (const heading of [
      "Real project scenario",
      "Debugging checklist",
      "Common production mistakes",
      "Interview / project review question"
    ]) {
      assert.equal(await lesson.getByRole("heading", { name: heading }).count(), 1, `lesson ${i + 1}: missing ${heading}`);
    }
    const sections = await lesson.locator(".mini").allTextContents();
    assert.ok(sections.length >= 5, `lesson ${i + 1}: expected practice and production-depth content`);
    assert.ok(sections.every(text => text.trim().length > 20), `lesson ${i + 1}: empty or too-short guidance section`);
  }
  await page.locator("#navList button").first().click();
  const englishLessonText = await page.locator("#lesson").innerText();
  await page.locator('[data-language="tinglish"]').click();
  const tinglishLessonText = await page.locator("#lesson").innerText();
  assert.notEqual(tinglishLessonText, englishLessonText, "language switch should change the lesson explanation");
  assert.match(tinglishLessonText, /INTERVIEW-READY ARCHITECTURE/i, "Tinglish deep explanation should render");
  assert.deepEqual(errors, [], `browser JavaScript errors: ${errors.join("; ")}`);

  console.log("Browser smoke tests passed: course navigation, diagnostic scenarios, English/Tinglish, 23 Snowflake production-depth lessons, mobile overflow, and no uncaught JS errors.");
} finally {
  await browser.close();
}
