import { test, expect } from '@playwright/test';

// Example Playwright test template that extracts DOM elements and posts them
// to the vision detection API. Use with the templating engine in the project.

test('{{ test_name }}', async ({ page, request }) => {
  await page.goto('{{ url }}');

  // Extract DOM nodes (same logic as app/templates/dom_extractor.js)
  const dom = await page.evaluate(() => {
    function isVisible(el) {
      if (!el) return false;
      const style = window.getComputedStyle(el);
      if (style.visibility === 'hidden' || style.display === 'none' || parseFloat(style.opacity || '1') === 0) return false;
      const rect = el.getBoundingClientRect();
      if (rect.width === 0 || rect.height === 0) return false;
      return true;
    }

    const tags = ['button','input','a','select','textarea','label','option'];
    const candidates = Array.from(document.querySelectorAll(tags.join(',')));

    return candidates
      .filter(isVisible)
      .map(el => {
        const r = el.getBoundingClientRect();
        const text = (el.innerText || el.value || el.getAttribute('aria-label') || el.getAttribute('alt') || '').toString().trim();
        return {
          tag: el.tagName.toLowerCase(),
          text: text || null,
          x: r.left + window.scrollX,
          y: r.top + window.scrollY,
          width: r.width,
          height: r.height,
          id: el.id || null,
          class: el.className || null,
          name: el.getAttribute('name') || null,
          role: el.getAttribute('role') || null
        };
      });
  });

  // Optional: take a screenshot to submit alongside DOM (server expects image_path)
  const screenshotPath = '{{ screenshot_path }}';
  if (screenshotPath && screenshotPath !== 'None') {
    await page.screenshot({ path: screenshotPath, fullPage: true });
  }

  // Post to detection API (adjust URL and port as needed)
  const detectUrl = '{{ detect_url }}';
  const response = await request.post(detectUrl, {
    data: {
      image_path: screenshotPath,
      include_ocr: {{ include_ocr | default(false) }},
      target_text: {{ target_text | default('null') }},
      min_confidence: {{ min_confidence | default(0.25) }},
      dom: dom,
    },
  });

  const body = await response.json();
  console.log('Detection response:', body);
  expect(response.ok()).toBeTruthy();
});
