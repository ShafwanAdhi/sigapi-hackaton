import { expect,test } from '@playwright/test';

const slug='12345678123442348234123456789abc';
const incident={reference:'SIGAPI-TEST',title:'Laporan kebakaran hutan/lahan',location_name:'Kota Malang',
  location:{latitude:-7.98,longitude:112.63},observed_at:null,location_version:1,photo_url:null,
  summary:'Laporan warga, belum dikonfirmasi resmi.',verification:{summary:'none',solved_claim_status:'none'}};
test.beforeEach(async({page})=>{
  await page.route('https://tile.openstreetmap.org/**',route=>route.fulfill({contentType:'image/png',body:Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/dEkAAAAASUVORK5CYII=','base64')}));
});

test('live GPS confirmation sends real form fields and displays only server receipt',async({page,context})=>{
  await context.grantPermissions(['geolocation']);await context.setGeolocation({latitude:-7.98,longitude:112.63,accuracy:20});
  let submitted='';
  await page.route('**/api/laporan/'+slug,route=>route.fulfill({json:incident}));
  await page.route('**/api/laporan/'+slug+'/verifications',async route=>{
    submitted=route.request().postData()??'';
    await route.fulfill({status:201,json:{receipt_id:'real-server-receipt',replayed:false}});
  });
  await page.goto('/laporan/'+slug,{waitUntil:'domcontentloaded'});
  await expect(page.locator('.page-label')).toContainText('SIGAPI-TEST');
  await page.getByRole('button',{name:'Aktifkan Lokasi'}).click();
  await page.getByLabel('Ya, kejadian benar terjadi').check();
  await page.getByRole('button',{name:/Kirim Konfirmasi/}).click();
  await expect(page.getByText(/real-server-receipt/)).toBeVisible();
  expect(submitted).toContain('gps_fix_at');expect(submitted).toContain('location_version');
  expect(submitted).toContain('request_id');
});

test('server GPS rejection preserves answer without a success receipt',async({page,context})=>{
  await context.grantPermissions(['geolocation']);await context.setGeolocation({latitude:-7.98,longitude:112.63,accuracy:20});
  await page.route('**/api/laporan/'+slug,route=>route.fulfill({json:incident}));
  await page.route('**/api/laporan/'+slug+'/verifications',route=>route.fulfill({status:422,json:{detail:'OUT_OF_RADIUS'}}));
  await page.goto('/laporan/'+slug,{waitUntil:'domcontentloaded'});await page.getByRole('button',{name:'Aktifkan Lokasi'}).click();
  await page.getByLabel('Tidak, informasi kejadian tidak sesuai').check();
  await page.getByRole('button',{name:/Kirim Konfirmasi/}).click();
  await expect(page.getByRole('alert')).toContainText('2 km');
  await expect(page.getByLabel('Tidak, informasi kejadian tidak sesuai')).toBeChecked();
  await expect(page.getByText(/Konfirmasi tersimpan/)).toHaveCount(0);
});
