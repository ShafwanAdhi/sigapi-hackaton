import {expect,test} from '@playwright/test';
test('admin login loads real API overview and all five navigation workspaces',async({page})=>{
  await page.route('https://tile.openstreetmap.org/**',route=>route.fulfill({contentType:'image/png',body:Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/dEkAAAAASUVORK5CYII=','base64')}));
  let authenticated=false;
  await page.route('**/api/admin/**',async route=>{
    const url=route.request().url();
    if(url.endsWith('/auth/login')){authenticated=true;return route.fulfill({json:{csrf_token:'test-csrf'}});}
    if(!authenticated)return route.fulfill({status:401,json:{detail:'AUTH_REQUIRED'}});
    if(url.endsWith('/auth/me'))return route.fulfill({json:{username:'admin-test',region_code:'35.73',csrf_token:'test-csrf'}});
    if(url.includes('/overview'))return route.fulfill({json:{region_code:'35.73',counts:{today:7,incomplete:2,unverified:3,forwarded:1},recent:[]}});
    if(url.includes('/map'))return route.fulfill({json:{reports:[],boundary:null,firms:null}});
    if(url.includes('/runtime'))return route.fulfill({json:{settings:{},analysis_jobs:[],approved_destinations:0,region_approved:false,live_gate:'pending',firms:{}}});
    return route.fulfill({json:{items:[],total:0}});
  });
  await page.goto('/admin/');
  await page.getByLabel('Username').fill('admin-test');await page.getByLabel('Password').fill('test-password');
  await page.getByRole('button',{name:'Masuk'}).click();
  await expect(page.getByRole('heading',{name:'Overview',exact:true})).toBeVisible();
  await expect(page.getByText('Laporan Hari Ini',{exact:true})).toBeVisible();
  for(const label of ['Laporan','Peta Kebakaran','Pihak Berwenang','Saluran MPA']){
    await page.getByRole('button',{name:label,exact:true}).click();
    await expect(page.getByRole('heading',{name:label,exact:true})).toBeVisible();
  }
  await page.screenshot({path:'../../.superpowers/sdd/2026-11-03-public-mvp/admin-desktop.png',fullPage:true});
});
