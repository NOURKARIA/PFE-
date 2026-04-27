import { test, expect } from '@playwright/test';

test('{{ test_name }}', async ({ page }) => {
{% for line in steps %}
  {{ line }}
{% endfor %}
});
