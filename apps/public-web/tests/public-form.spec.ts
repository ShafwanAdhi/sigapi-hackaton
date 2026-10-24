import { expect, test } from '@playwright/test';
import { mkdir } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';

const demoPath = '/laporan/demo-malang-001';

test('responsive page, local form interactions, location errors and screenshots', async ({ page }) => {
  const errors: string[] = [];
  const mutations: string[] = [];
  page.on('pageerror', error => errors.push(error.message));
  page.on('request', request => { if (request.method() === 'POST') mutations.push(request.url()); });
  await mkdir('artifacts', { recursive: true });
  await page.goto(demoPath);
  await expect(page.getByRole('heading', { name: 'Laporan kebakaran lahan', exact: true })).toBeVisible();
  await expect(page.getByText('Data simulasi', { exact: true })).toBeVisible();
  const incidentPhoto = page.getByRole('img', { name: /^Ilustrasi AI/ });
  await expect(incidentPhoto).toBeVisible();
  await expect.poll(() => incidentPhoto.evaluate((image: HTMLImageElement) => image.naturalWidth)).toBeGreaterThan(0);
  await expect(page.getByRole('img', { name: 'Peta skematis lokasi simulasi di Kota Malang' })).toBeVisible();

  for (const width of [360, 375, 390, 768, 1440]) {
    await page.setViewportSize({ width, height: 844 });
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
    await page.screenshot({ path: `artifacts/layout-${width}.png`, fullPage: true });
  }

  await page.setViewportSize({ width: 390, height: 844 });
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({ path: 'artifacts/01-overview-mobile.png' });
  await page.locator('.incident-photo').evaluate(element => element.scrollIntoView());
  await page.screenshot({ path: 'artifacts/01b-photo-map-mobile.png' });
  await page.getByRole('link', { name: 'Berikan konfirmasi' }).click();
  await expect(page.locator('#konfirmasi')).toBeFocused();
  const submit = page.getByRole('button', { name: 'Coba kirim konfirmasi' });
  await expect(submit).toBeDisabled();
  await page.getByRole('radio', { name: /Ya, benar terjadi/ }).check();
  const solved = page.getByRole('checkbox', { name: /Berdasarkan pengamatan saya/ });
  await expect(solved).not.toBeChecked();
  await solved.check();
  await page.getByRole('radio', { name: /Tidak, kondisi tidak sesuai/ }).check();
  await expect(solved).toHaveCount(0);
  await page.locator('.choice-fieldset').evaluate(element => element.scrollIntoView());
  await page.screenshot({ path: 'artifacts/02b-invalid-mobile.png' });
  await page.getByRole('radio', { name: /Ya, benar terjadi/ }).check();
  await expect(solved).not.toBeChecked();
  await page.getByLabel('Keterangan tambahan').fill('Asap masih terlihat dari jalan. Saya berada di tempat aman.');

  await page.getByLabel('Coba kondisi lokasi').selectOption('denied');
  await page.getByRole('button', { name: 'Coba lokasi simulasi' }).click();
  await expect(page.getByText('Izin lokasi belum diberikan', { exact: true })).toBeVisible();
  await expect(submit).toBeDisabled();
  await page.getByLabel('Coba kondisi lokasi').selectOption('outside');
  await page.getByRole('button', { name: 'Coba lokasi simulasi' }).click();
  await expect(page.getByText('Di luar radius 2 km', { exact: true })).toBeVisible();
  await expect(submit).toBeDisabled();
  await page.locator('#konfirmasi').evaluate(element => element.scrollIntoView());
  await page.screenshot({ path: 'artifacts/03-location-error-mobile.png' });
  await expect(page.getByRole('radio', { name: /Ya, benar terjadi/ })).toBeChecked();
  await page.getByLabel('Coba kondisi lokasi').selectOption('ready');
  await page.getByRole('button', { name: 'Coba lokasi simulasi' }).click();
  await expect(submit).toBeEnabled();
  await page.locator('#konfirmasi').evaluate(element => element.scrollIntoView());
  await page.screenshot({ path: 'artifacts/02-confirmation-mobile.png' });

  const upload = page.getByLabel('Foto kondisi lapangan');
  await upload.setInputFiles({ name: 'oversized.webp', mimeType: 'image/webp', buffer: Buffer.alloc(10 * 1024 * 1024 + 1) });
  await expect(page.getByRole('alert')).toContainText('maksimal 10 MB');
  await upload.setInputFiles({ name: 'corrupt.png', mimeType: 'image/png', buffer: Buffer.from('not-an-image') });
  await expect(page.getByRole('alert')).toContainText('Foto tidak dapat dibuka');
  await expect(submit).toBeDisabled();
  const fileChooserPromise = page.waitForEvent('filechooser');
  await page.getByRole('button', { name: 'Pilih foto' }).click();
  const fileChooser = await fileChooserPromise;
  await fileChooser.setFiles(fileURLToPath(new URL('../public/media/incident-simulation.webp', import.meta.url)));
  await expect(page.getByRole('img', { name: 'Preview foto kondisi lapangan yang Anda pilih' })).toBeVisible();
  await expect(submit).toBeEnabled();
  await submit.click();
  await expect(page.getByText('Simulasi selesai · belum dikirim', { exact: true })).toBeVisible();
  await expect(page.locator('.preview-result')).toBeFocused();
  expect(mutations).toEqual([]);
  await page.screenshot({ path: 'artifacts/04-preview-mobile.png' });
  await page.getByRole('button', { name: 'Hapus foto' }).click();
  await expect(page.getByRole('img', { name: 'Preview foto kondisi lapangan yang Anda pilih' })).toHaveCount(0);
  await expect(page.getByText('Simulasi selesai · belum dikirim', { exact: true })).toHaveCount(0);
  expect(errors).toEqual([]);
});

test('root alias, keyboard access and unavailable report', async ({ page }) => {
  await page.goto('/');
  await expect(page).toHaveURL(new RegExp(`${demoPath}$`));
  await page.keyboard.press('Tab');
  await expect(page.getByRole('link', { name: 'Lewati ke konten utama' })).toBeFocused();
  await page.getByRole('radio', { name: /Ya, benar terjadi/ }).focus();
  await page.keyboard.press('Space');
  await expect(page.getByRole('checkbox', { name: /Berdasarkan pengamatan saya/ })).toBeVisible();
  await page.goto('/laporan/tidak-tersedia');
  await expect(page.getByRole('heading', { name: 'Laporan tidak tersedia.' })).toBeVisible();
  await expect(page.getByText('SIGAPI-DEMO-001')).toHaveCount(0);
});

test('landscape and reduced motion preserve the form layout', async ({ page }) => {
  await page.emulateMedia({ reducedMotion: 'reduce', colorScheme: 'dark' });
  await page.setViewportSize({ width: 844, height: 390 });
  await page.goto(demoPath);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  // The prototype deliberately keeps its light theme when the OS is in dark mode.
  expect(await page.locator('body').evaluate(element => getComputedStyle(element).colorScheme)).toBe('light');
  await page.getByRole('link', { name: 'Berikan konfirmasi' }).click();
  await expect(page.locator('#konfirmasi')).toBeFocused();
  await page.getByRole('radio', { name: /Ya, benar terjadi/ }).check();
  await expect(page.getByRole('checkbox', { name: /Berdasarkan pengamatan saya/ })).toBeVisible();
});
