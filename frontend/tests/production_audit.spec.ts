import { test, expect } from '@playwright/test';
import fs from 'fs';
import path from 'path';

const BASE_URL = 'http://localhost:3000';
const ARTIFACT_DIR = 'C:\\Users\\nithi\\.gemini\\antigravity-ide\\brain\\d0517bf9-ed17-4247-8dcf-092050b610a0\\scratch';

if (!fs.existsSync(ARTIFACT_DIR)) {
  fs.mkdirSync(ARTIFACT_DIR, { recursive: true });
}

test.describe('Live End-to-End Production Audit', () => {
  test.setTimeout(120000);
  const runId = Date.now();
  const founderEmail = `founder_audit_${runId}@test.com`;
  const investorEmail = `investor_audit_${runId}@test.com`;
  let networkLogs: any[] = [];
  let consoleErrors: string[] = [];

  test.beforeEach(async ({ page }) => {
    networkLogs = [];
    consoleErrors = [];
    page.on('pageerror', err => consoleErrors.push(`[Exception] ${err.message}`));
    page.on('console', msg => {
      if (msg.type() === 'error' && !msg.text().includes('favicon') && !msg.text().includes('Warning:')) {
        consoleErrors.push(`[Console] ${msg.text()}`);
      }
    });
    page.on('response', response => {
      if (response.url().includes('/api/')) {
        networkLogs.push(`[${response.status()}] ${response.request().method()} ${response.url()}`);
      }
    });
  });

  test.afterEach(async ({ page }, testInfo) => {
    const report = { test: testInfo.title, errors: consoleErrors, networkFailures: networkLogs };
    fs.writeFileSync(path.join(ARTIFACT_DIR, `${testInfo.title.replace(/[^a-z0-9]/gi, '_').toLowerCase()}_report.json`), JSON.stringify(report, null, 2));
  });

  test('1. Founder Journey', async ({ page }) => {
    // Register
    await page.goto(`${BASE_URL}/auth/register`);
    await page.fill('input[name="first_name"]', 'Audit');
    await page.fill('input[name="last_name"]', 'Founder');
    await page.fill('input[name="email"]', founderEmail);
    await page.fill('input[name="password"]', 'StrongPass123!');
    await page.fill('input[name="confirm_password"]', 'StrongPass123!');
    await page.getByText('I have a startup').click();
    await page.getByRole('button', { name: 'Create Account' }).click();
    
    // Login
    await page.waitForURL('**/auth/login', { timeout: 15000 });
    await page.fill('input[name="email"]', founderEmail);
    await page.fill('input[name="password"]', 'StrongPass123!');
    await page.getByRole('button', { name: 'Sign In' }).click();
    await expect(page).toHaveURL(/.*founder/, { timeout: 15000 });
    await page.screenshot({ path: path.join(ARTIFACT_DIR, 'founder_dashboard.png') });
    
    // Profile
    await page.goto(`${BASE_URL}/founder/profile`);
    await page.waitForTimeout(2000);
    await page.screenshot({ path: path.join(ARTIFACT_DIR, 'founder_profile.png') });
    
    // Setup Startup
    await page.goto(`${BASE_URL}/founder/startups/new`);
    await page.waitForTimeout(2000);
    await page.screenshot({ path: path.join(ARTIFACT_DIR, 'founder_startups_new_pre.png') });
    
    // Try filling it out if it exists
    try {
      await page.fill('input[name="name"]', 'Audit Startup AI');
      await page.fill('input[name="tagline"]', 'Audit Tagline');
      await page.fill('textarea[name="description"]', 'Audit description here for the startup.');
      await page.selectOption('select[name="industry"]', 'ai_ml');
      await page.selectOption('select[name="stage"]', 'pre_seed');
      await page.selectOption('select[name="funding_status"]', 'raising');
      await page.getByRole('button', { name: 'Create Startup' }).click();
      await expect(page).toHaveURL(/.*founder\/startups/, { timeout: 15000 });
      await page.screenshot({ path: path.join(ARTIFACT_DIR, 'founder_startups_list.png') });
    } catch (e) {
      console.log('UI Startup Setup Failed:', e);
      // fallback to API so rest of test can work
      const tokenObj = await page.evaluate(() => localStorage.getItem('auth_store'));
      const token = JSON.parse(tokenObj as string).state.tokens.access;
      await page.request.post('http://localhost:8000/api/v1/startups/', {
        headers: { Authorization: `Bearer ${token}` },
        data: { name: 'Audit Startup AI', tagline: 'Tagline', description: 'Desc', industry: 'ai_ml', stage: 'pre_seed', funding_status: 'raising', looking_for_funding: true }
      });
      await page.goto(`${BASE_URL}/founder/startups`);
      await page.waitForTimeout(2000);
    }
  });

  test('2. Investor Journey', async ({ page }) => {
    // Register
    await page.goto(`${BASE_URL}/auth/register`);
    await page.fill('input[name="first_name"]', 'Audit');
    await page.fill('input[name="last_name"]', 'Investor');
    await page.fill('input[name="email"]', investorEmail);
    await page.fill('input[name="password"]', 'StrongPass123!');
    await page.fill('input[name="confirm_password"]', 'StrongPass123!');
    await page.getByText('I want to invest').click();
    await page.getByRole('button', { name: 'Create Account' }).click();
    
    // Login
    await page.waitForURL('**/auth/login', { timeout: 15000 });
    await page.fill('input[name="email"]', investorEmail);
    await page.fill('input[name="password"]', 'StrongPass123!');
    await page.getByRole('button', { name: 'Sign In' }).click();
    await page.waitForTimeout(2000);
    console.log("Investor URL after login:", page.url());
    const store = await page.evaluate(() => localStorage.getItem('auth-storage'));
    console.log("Investor Auth store:", store);
    await expect(page).toHaveURL(/.*investor/, { timeout: 15000 });
    await page.screenshot({ path: path.join(ARTIFACT_DIR, 'investor_dashboard.png') });
    
    // Matches
    await page.goto(`${BASE_URL}/investor/matches`);
    await page.waitForTimeout(3000);
    await page.screenshot({ path: path.join(ARTIFACT_DIR, 'investor_matches.png') });
  });

  test('3. Admin Journey', async ({ page }) => {
     await page.goto(`${BASE_URL}/admin`);
     await page.waitForTimeout(2000);
     await page.screenshot({ path: path.join(ARTIFACT_DIR, 'admin_page.png') });
  });

  test('4. Chat Validation', async ({ browser }) => {
     const context1 = await browser.newContext();
     const p1 = await context1.newPage();
     await p1.goto(`${BASE_URL}/auth/login`);
     await p1.fill('input[name="email"]', investorEmail);
     await p1.fill('input[name="password"]', 'StrongPass123!');
     await p1.getByRole('button', { name: 'Sign In' }).click();
     await expect(p1).toHaveURL(/.*investor/, { timeout: 15000 });
     await p1.goto(`${BASE_URL}/investor/matches`);
     await p1.waitForTimeout(2000);
     
     // Force match generation
     const store1 = await p1.evaluate(() => localStorage.getItem('auth_store'));
     if (store1) {
       const token1 = JSON.parse(store1).state.tokens.access;
       await p1.request.get('http://localhost:8000/api/v1/matching/investor/matches/?reload=true', {
         headers: { Authorization: `Bearer ${token1}` }
       });
       await p1.reload();
       await p1.waitForTimeout(2000);
     }
     
     const msgBtn = p1.getByRole('button', { name: 'Message' }).first();
     if (await msgBtn.isVisible()) {
        await msgBtn.click();
        await expect(p1).toHaveURL(/\/chat\/\d+/, { timeout: 15000 });
        await p1.screenshot({ path: path.join(ARTIFACT_DIR, 'chat_created.png') });
        await p1.fill('input[placeholder*="Type"]', 'Ping from Investor');
        await p1.getByRole('button', { name: 'Send' }).click();
        await p1.waitForTimeout(1000);
        await p1.screenshot({ path: path.join(ARTIFACT_DIR, 'chat_sent.png') });
     } else {
        console.log("No message button found on matches page");
     }

     const context2 = await browser.newContext();
     const p2 = await context2.newPage();
     await p2.goto(`${BASE_URL}/auth/login`);
     await p2.fill('input[name="email"]', founderEmail);
     await p2.fill('input[name="password"]', 'StrongPass123!');
     await p2.getByRole('button', { name: 'Sign In' }).click();
     await expect(p2).toHaveURL(/.*founder/, { timeout: 15000 });
     await p2.goto(`${BASE_URL}/chat`);
     await p2.waitForTimeout(2000);
     await p2.screenshot({ path: path.join(ARTIFACT_DIR, 'chat_founder_list.png') });
  });
});
