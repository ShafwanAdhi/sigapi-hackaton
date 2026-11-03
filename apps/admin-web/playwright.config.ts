import {defineConfig} from '@playwright/test';
export default defineConfig({testDir:'./tests',workers:1,use:{baseURL:'http://127.0.0.1:5180',launchOptions:{channel:'msedge'},screenshot:'only-on-failure'},webServer:{command:'npm run dev',url:'http://127.0.0.1:5180/admin/',reuseExistingServer:!process.env.CI}});
