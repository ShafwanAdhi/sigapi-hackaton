import { expect, test } from '@playwright/test';
import { mkdir } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';

const demoPath = '/laporan/demo-insiden-sigapi';
const validLabel = 'Ya, kejadian benar terjadi';
const invalidLabel = 'Tidak, informasi kejadian tidak sesuai';

test('public page structure, mobile-to-desktop layout and screenshots', async ({ page }) => {
  const errors: string[] = [];
  page.on('pageerror', error => errors.push(error.message));
  page.on('console', message => { if (message.type() === 'error') errors.push(message.text() + ' ' + message.location().url); });
  await mkdir('artifacts', { recursive: true });
  await page.goto(demoPath);
  await page.evaluate(() => document.fonts.ready);
  await expect(page.getByRole('heading', { level: 1, name: 'Konfirmasi Laporan Kebakaran' })).toBeVisible();
  await expect(page.locator('.page-label')).toHaveText('Nomor laporan: SIGAPI-001');
  await expect(page.getByText('Belum dikonfirmasi resmi', { exact: true })).toBeVisible();
  await expect(page.getByText('Waktu kejadian: Belum tersedia', { exact: true })).toBeVisible();
  await expect(page.locator('body')).not.toContainText(/simulasi|prototipe|sintetis|demonstrasi|backend|DEMO/i);
  await expect(page.locator('.simulation-controls, .simulation-note, .prototype-note, .footer-simulation')).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Aktifkan Lokasi', exact: true })).toBeDisabled();
  await expect(page.getByRole('button', { name: 'Aktifkan Lokasi', exact: true })).toHaveCSS('background-color', 'rgb(200, 75, 27)');
  await expect(page.getByRole('button', { name: 'Kirim Konfirmasi', exact: true })).toHaveCSS('background-color', 'rgb(200, 75, 27)');
  await expect(page.locator('.submit-hint')).toHaveCount(0);
  await expect(page.getByRole('radio', { name: validLabel, exact: true })).not.toBeChecked();
  await expect(page.getByRole('radio', { name: invalidLabel, exact: true })).not.toBeChecked();
  const incidentPhoto = page.getByRole('img', { name: 'Asap dan api pada lahan berumput.', exact: true });
  await expect.poll(() => incidentPhoto.evaluate((image: HTMLImageElement) => image.naturalWidth)).toBeGreaterThan(0);
  await expect(page.getByRole('img', { name: 'Lokasi kejadian di Kota Malang' })).toBeVisible();

  const headings = await page.locator('main h2, fieldset legend').allTextContents();
  expect(headings).toEqual(['Informasi Kejadian', 'Lokasi Kejadian', 'Konfirmasi Lokasi Anda', 'Apakah kejadian benar terjadi?']);

  for (const width of [320, 360, 390, 768, 1024, 1100, 1280, 1440, 1920]) {
    await page.setViewportSize({ width, height: 844 });
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
    const sections = await page.locator('.incident-card, .incident-location-card, .geolocation-card, .confirmation-card').evaluateAll(elements => elements.map(element => {
      const rect = element.getBoundingClientRect();
      return { x: rect.x, right: rect.right, width: rect.width, top: rect.top, bottom: rect.bottom };
    }));
    const context = await page.locator('.incident-context').boundingBox();
    if (width < 1100) {
      for (let i = 1; i < sections.length; i++) {
        expect(sections[i].top).toBeGreaterThanOrEqual(sections[i - 1].bottom);
        expect(sections[i].x).toBe(i === 1 ? sections[0].x : context!.x);
      }
      expect(sections[0].x).toBeGreaterThanOrEqual(context!.x);
      expect(sections[0].right).toBeLessThanOrEqual(context!.x + context!.width);
    } else {
      const [incident, map, location, confirmation] = sections;
      expect(location.x).toBeGreaterThan(incident.right);
      expect(location.top).toBeCloseTo(context!.y, 0);
      expect(map.top).toBeGreaterThanOrEqual(incident.bottom);
      expect(confirmation.top).toBeGreaterThan(location.bottom);
      expect(confirmation.x).toBe(location.x);
      expect(confirmation.width).toBeGreaterThan(incident.width);
    }
    if (width >= 1100) expect(await page.locator('main').evaluate(el => el.getBoundingClientRect().width)).toBeLessThanOrEqual(1184);
    const header = await page.locator('.site-header').boundingBox();
    const description = await page.locator('.page-intro > p').boundingBox();
    expect(description!.y + description!.height).toBeLessThan(header!.y + header!.height);
    expect(sections[0].top).toBeGreaterThanOrEqual(header!.y + header!.height);
    const dimensions = await incidentPhoto.boundingBox();
    expect(dimensions!.width / dimensions!.height).toBeCloseTo(16 / 9, 1);
    await page.screenshot({ path: 'artifacts/header-desktop-layout-' + width + '.png', fullPage: true });
  }

  await page.setViewportSize({ width: 390, height: 844 });
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({ path: 'artifacts/capture-01-incident-mobile.png' });
  await page.locator('.incident-location-card').evaluate(element => element.scrollIntoView());
  await page.screenshot({ path: 'artifacts/capture-02-map-location-mobile.png' });
  await page.locator('.confirmation-card').evaluate(element => element.scrollIntoView());
  await page.screenshot({ path: 'artifacts/capture-03-form-mobile.png' });
  await page.locator('.confirmation-card').screenshot({ path: 'artifacts/capture-03b-form-card-mobile.png' });
  expect(errors).toEqual([]);
});

test('location simulation, loading, retries, cancellation and disabled real submission', async ({ page }) => {
  const posts: string[] = [];
  await page.addInitScript(() => {
    // Any accidental device GPS request fails this test immediately.
    navigator.geolocation.getCurrentPosition = () => { throw new Error('Device geolocation must not be called'); };
    navigator.geolocation.watchPosition = () => { throw new Error('Device geolocation must not be called'); };
  });
  const errors: string[] = [];
  page.on('pageerror', error => errors.push(error.message));
  page.on('request', request => { if (request.method() === 'POST') posts.push(request.url()); });
  await page.goto(demoPath + '?dev=1');
  const submit = page.getByRole('button', { name: 'Kirim Konfirmasi', exact: true });
  await expect(submit).toBeDisabled();
  await expect(page.getByText('Lokasi belum diperiksa', { exact: true })).toBeVisible();
  await page.getByRole('radio', { name: validLabel, exact: true }).check();
  await page.getByLabel('Keterangan tambahan').fill('Saya mengamati dari tempat aman.');
  await page.getByRole('button', { name: 'Aktifkan Lokasi', exact: true }).click();
  await expect(page.getByRole('status')).toContainText('Sedang mengambil lokasi perangkat...');
  await expect(page.getByRole('button', { name: 'Mengambil Lokasi...' })).toBeDisabled();
  await expect(page.getByRole('status')).toContainText('Lokasi Anda memenuhi persyaratan konfirmasi.');
  await expect(page.getByRole('status')).toContainText('Hasil simulasi');
  await expect(submit).toBeDisabled();

  await page.getByText('Pengaturan simulasi lokasi', { exact: true }).click();
  const setting = page.getByLabel('Kondisi yang ingin dicoba');
  for (const outcome of ['denied', 'outside', 'inaccurate'] as const) {
    await setting.selectOption(outcome);
    await page.getByRole('button', { name: 'Aktifkan Lokasi', exact: true }).click();
    await expect(page.getByRole('status')).toContainText(outcome === 'denied' ? 'Izin lokasi ditolak' : outcome === 'outside' ? 'Di luar radius konfirmasi' : 'Akurasi lokasi belum memadai');
    await expect(page.getByRole('button', { name: 'Coba Lagi', exact: true })).toBeEnabled();
    await expect(submit).toBeDisabled();
    await expect(page.getByRole('radio', { name: validLabel, exact: true })).toBeChecked();
    await expect(page.getByLabel('Keterangan tambahan')).toHaveValue('Saya mengamati dari tempat aman.');
  }
  await page.locator('.geolocation-card').evaluate(element => element.scrollIntoView());
  await page.screenshot({ path: 'artifacts/capture-04-location-error-mobile.png' });

  // Changing the demo outcome cancels any pending response from the older request.
  await setting.selectOption('outside');
  await page.getByRole('button', { name: 'Aktifkan Lokasi', exact: true }).click();
  await setting.selectOption('ready');
  await expect(page.getByRole('status')).toContainText('Lokasi belum diperiksa');
  await page.getByRole('button', { name: 'Aktifkan Lokasi', exact: true }).click();
  await expect(page.getByRole('status')).toContainText('Lokasi Anda memenuhi persyaratan konfirmasi.');
  await expect(submit).toBeDisabled();
  expect(posts).toEqual([]);
  expect(errors).toEqual([]);
});

test('valid-only solved claim and local photo preview work without a fake receipt', async ({ page }) => {
  await page.goto(demoPath);
  await page.getByRole('radio', { name: validLabel, exact: true }).check();
  const solved = page.getByRole('checkbox', { name: /Kebakaran sudah tertangani/ });
  await expect(solved).not.toBeChecked();
  await solved.check();
  await page.getByRole('radio', { name: invalidLabel, exact: true }).check();
  await expect(solved).toHaveCount(0);
  await expect(page.locator('.choice-invalid')).toHaveClass(/selected/);
  await expect(page.locator('input[value="invalid"]')).not.toHaveAttribute('aria-invalid', 'true');
  await page.locator('.confirmation-card').evaluate(element => element.scrollIntoView());
  await page.screenshot({ path: 'artifacts/capture-05-invalid-mobile.png' });
  await page.getByRole('radio', { name: validLabel, exact: true }).check();
  await expect(solved).not.toBeChecked();

  const description = page.getByLabel('Keterangan tambahan');
  await description.fill('Asap masih terlihat dari jalan yang aman.');
  const upload = page.getByLabel('Tambahkan Foto');
  await upload.setInputFiles({ name: 'oversized.webp', mimeType: 'image/webp', buffer: Buffer.alloc(10 * 1024 * 1024 + 1) });
  await expect(page.getByRole('alert')).toContainText('maksimal 10 MB');
  await upload.setInputFiles({ name: 'broken.png', mimeType: 'image/png', buffer: Buffer.from('not-an-image') });
  await expect(page.getByRole('alert')).toContainText('Foto tidak dapat dibuka');
  const chooserPromise = page.waitForEvent('filechooser');
  await page.getByRole('button', { name: 'Pilih foto dari perangkat' }).click();
  const chooser = await chooserPromise;
  await chooser.setFiles(fileURLToPath(new URL('../public/media/incident-simulation.webp', import.meta.url)));
  await expect(page.getByRole('img', { name: 'Preview foto kondisi lapangan yang Anda pilih' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Kirim Konfirmasi', exact: true })).toBeDisabled();
  await page.locator('.confirmation-card').evaluate(element => element.scrollIntoView());
  await page.screenshot({ path: 'artifacts/capture-06-valid-photo-mobile.png', fullPage: true });
  await page.getByRole('button', { name: 'Hapus foto', exact: true }).click();
  await expect(page.getByRole('img', { name: 'Preview foto kondisi lapangan yang Anda pilih' })).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Pilih foto dari perangkat' })).toBeFocused();
  await expect(description).toHaveValue('Asap masih terlihat dari jalan yang aman.');
  await expect(page.getByText(/Konfirmasi berhasil disimpan|Simulasi selesai/)).toHaveCount(0);
});

test('route compatibility, keyboard, reduced motion and narrow reflow', async ({ page }) => {
  await page.emulateMedia({ reducedMotion: 'reduce', colorScheme: 'dark' });
  await page.goto('/');
  await expect(page).toHaveURL(new RegExp(demoPath + '$'));
  await page.keyboard.press('Tab');
  await expect(page.getByRole('link', { name: 'Lewati ke konten utama' })).toBeFocused();
  const valid = page.getByRole('radio', { name: validLabel, exact: true });
  await valid.focus();
  await page.keyboard.press('Space');
  const solved = page.getByRole('checkbox', { name: /Kebakaran sudah tertangani/ });
  await solved.focus();
  await page.keyboard.press('Space');
  await expect(solved).toBeChecked();
  const description = page.getByLabel('Keterangan tambahan');
  await description.focus();
  await expect(description).toHaveCSS('outline-color', 'rgb(200, 75, 27)');
  await expect(description).toHaveAccessibleDescription(/Tuliskan apa yang Anda lihat dari tempat aman/);
  expect(await page.locator('.solved-block').evaluate(element => getComputedStyle(element).animationName)).toBe('none');
  for (const size of [{ width: 844, height: 390 }, { width: 320, height: 844 }]) {
    await page.setViewportSize(size);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  }
  await page.setViewportSize({ width: 720, height: 844 });
  await page.evaluate(() => { document.body.style.zoom = '2'; });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.goto('/laporan/demo-malang-001');
  await expect(page.getByRole('heading', { level: 1, name: 'Konfirmasi Laporan Kebakaran' })).toBeVisible();
  await page.goto('/laporan/tidak-tersedia');
  await expect(page.getByRole('heading', { name: 'Laporan tidak tersedia.' })).toBeVisible();
  await expect(page.getByText('SIGAPI-001')).toHaveCount(0);
});
