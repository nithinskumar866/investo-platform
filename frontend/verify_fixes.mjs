import { chromium } from '@playwright/test';
import fs from 'fs';

const BASE_URL = 'http://localhost:3000';
const ARTIFACT_DIR = 'C:\\Users\\nithi\\.gemini\\antigravity-ide\\brain\\fd444762-25ce-4671-ac6b-7e9ab7e0e2fd\\scratch';

if (!fs.existsSync(ARTIFACT_DIR)) {
  fs.mkdirSync(ARTIFACT_DIR, { recursive: true });
}

const report = {
  startups: { apiResponse: null, errors: [], success: false, screenshot: '' },
  chat: { apiResponse: null, sendSuccess: false, errors: [], success: false, screenshot: '' },
  matches: { founder: { errors: [], success: false, screenshot: '' }, investor: { errors: [], success: false, screenshot: '' } }
};

async function run() {
  console.log("Launching browser...");
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();

  // Helper for capturing errors
  page.on('pageerror', err => console.log(`[Error] ${err.message}`));
  
  // 1. Founder Login
  console.log("Logging in as Founder...");
  await page.goto(`${BASE_URL}/auth/login`);
  await page.fill('input[type="email"]', 'founder@test.com');
  await page.fill('input[type="password"]', 'password123');
  await page.click('button[type="submit"]');
  await page.waitForURL('**/founder', { timeout: 15000 });
  await page.waitForTimeout(2000);

  // 1.1 Startups Verification
  console.log("Verifying Startups...");
  let startupsPromise = page.waitForResponse(res => res.url().includes('/api/v1/startups/') && res.request().method() === 'GET');
  await page.goto(`${BASE_URL}/founder/startups`, { waitUntil: 'domcontentloaded' });
  let startupsRes = await startupsPromise;
  report.startups.apiResponse = { status: startupsRes.status(), body: await startupsRes.json().catch(()=>null) };
  await page.waitForTimeout(2000);
  report.startups.screenshot = `${ARTIFACT_DIR}\\verification_startups.png`;
  await page.screenshot({ path: report.startups.screenshot });
  report.startups.success = report.startups.apiResponse.status === 200 && Array.isArray(report.startups.apiResponse.body);

  // 1.2 Matches Verification (Founder)
  console.log("Verifying Founder Matches...");
  let fMatchPromise = page.waitForResponse(res => res.url().includes('/api/v1/matching/') && res.request().method() === 'GET');
  await page.goto(`${BASE_URL}/founder/matches`, { waitUntil: 'domcontentloaded' });
  let fMatchRes = await fMatchPromise;
  report.matches.founder.apiResponse = { status: fMatchRes.status() };
  await page.waitForTimeout(2000);
  report.matches.founder.screenshot = `${ARTIFACT_DIR}\\verification_f_matches.png`;
  await page.screenshot({ path: report.matches.founder.screenshot });
  report.matches.founder.success = fMatchRes.status() === 200;
  if(fMatchRes.status() === 403) report.matches.founder.errors.push("403 Forbidden");

  // 1.3 Chat Verification
  console.log("Verifying Chat...");
  let chatPromise = page.waitForResponse(res => res.url().includes('/api/v1/chat/conversations/') && res.request().method() === 'GET');
  await page.goto(`${BASE_URL}/chat`, { waitUntil: 'domcontentloaded' });
  let chatRes = await chatPromise;
  report.chat.apiResponse = { status: chatRes.status(), body: await chatRes.json().catch(()=>null) };
  await page.waitForTimeout(2000);
  report.chat.screenshot = `${ARTIFACT_DIR}\\verification_chat.png`;
  await page.screenshot({ path: report.chat.screenshot });
  report.chat.success = chatRes.status() === 200;

  console.log("Clicking conversation...");
  const firstConv = await page.$('a[href^="/chat/"]');
  if (firstConv) {
    await firstConv.click();
    await page.waitForTimeout(2000);
    // Send a message
    const input = await page.$('input[placeholder*="message"], textarea[placeholder*="message"]');
    if (input) {
      console.log("Sending test message...");
      await input.fill('Verification test message');
      await page.keyboard.press('Enter');
      await page.waitForTimeout(1000);
      report.chat.sendSuccess = true;
    }
  }

  // 2. Investor Login
  console.log("Logging in as Investor...");
  await page.goto(`${BASE_URL}/auth/login`);
  await page.evaluate(() => localStorage.clear());
  await context.clearCookies();
  await page.goto(`${BASE_URL}/auth/login`);
  await page.waitForLoadState('domcontentloaded');
  await page.fill('input[type="email"]', 'investor@test.com');
  await page.fill('input[type="password"]', 'password123');
  await page.click('button[type="submit"]');
  await page.waitForURL('**/investor', { timeout: 15000 });
  await page.waitForTimeout(2000);

  // 2.1 Matches Verification (Investor)
  console.log("Verifying Investor Matches...");
  let iMatchPromise = page.waitForResponse(res => res.url().includes('/api/v1/matching/') && res.request().method() === 'GET');
  await page.goto(`${BASE_URL}/investor/matches`, { waitUntil: 'domcontentloaded' });
  let iMatchRes = await iMatchPromise;
  report.matches.investor.apiResponse = { status: iMatchRes.status() };
  await page.waitForTimeout(2000);
  report.matches.investor.screenshot = `${ARTIFACT_DIR}\\verification_i_matches.png`;
  await page.screenshot({ path: report.matches.investor.screenshot });
  report.matches.investor.success = iMatchRes.status() === 200;
  if(iMatchRes.status() === 403) report.matches.investor.errors.push("403 Forbidden");

  await browser.close();

  fs.writeFileSync(`${ARTIFACT_DIR}\\verification_report.json`, JSON.stringify(report, null, 2));
  console.log("DONE");
}

run().catch(e => console.error(e));
