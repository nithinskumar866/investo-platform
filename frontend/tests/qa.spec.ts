import { test, expect } from '@playwright/test';
import fs from 'fs';
import path from 'path';

const BASE_URL = 'http://localhost:3001';
const RESULTS: any[] = [];
const ARTIFACT_DIR = 'C:\\Users\\nithi\\.gemini\\antigravity-ide\\brain\\04970704-b4e2-4d7c-bdd2-48fa609bcf1a\\screenshots';

if (!fs.existsSync(ARTIFACT_DIR)) {
  fs.mkdirSync(ARTIFACT_DIR, { recursive: true });
}

test.describe.serial('Platform QA', () => {
  let errors: string[] = [];
  let apiFailures: string[] = [];

  test.beforeEach(async ({ page }) => {
    errors = [];
    apiFailures = [];
    page.on('pageerror', err => errors.push(`[Runtime] ${err.message}`));
    page.on('console', msg => {
      if (msg.type() === 'error' && !msg.text().includes('favicon') && !msg.text().includes('Warning:')) {
        errors.push(`[Console] ${msg.text()}`);
      }
    });
    page.on('response', response => {
      if (!response.ok() && response.url().includes('/api/') && response.request().method() === 'GET') {
        apiFailures.push(`[API ${response.status()}] ${response.url()}`);
      }
    });
  });

  async function checkPage(page, routePath, name) {
    let emptyScreen = false;
    let screenshotFile = '';
    try {
      await page.goto(`${BASE_URL}${routePath}`, { waitUntil: 'networkidle', timeout: 30000 });
      await page.waitForTimeout(2000); // let hydration and queries finish
      const content = await page.content();
      emptyScreen = content.includes('Application Error') || content.includes('An unexpected error has occurred');
      
      const safeName = name.replace(/[^a-z0-9]/gi, '_').toLowerCase();
      screenshotFile = `${ARTIFACT_DIR}\\${safeName}.png`;
      await page.screenshot({ path: screenshotFile, fullPage: true });

      RESULTS.push({
        Flow: name,
        Path: routePath,
        Pass: errors.length === 0 && apiFailures.length === 0 && !emptyScreen ? 'PASS' : 'FAIL',
        Errors: [...errors, ...apiFailures].slice(0, 3).join(' | ') || (emptyScreen ? '[Screen] Application Error' : ''),
        Screenshot: screenshotFile
      });
    } catch (e) {
      RESULTS.push({ Flow: name, Path: routePath, Pass: 'FAIL', Errors: `[Timeout/Crash] ${e.message}`, Screenshot: '' });
    }
    errors = [];
    apiFailures = [];
  }

  test('Founder Flow', async ({ page }) => {
    await page.goto(`${BASE_URL}/auth/login`);
    await page.fill('input[type="email"]', 'founder@test.com');
    await page.fill('input[type="password"]', 'password123');
    await page.click('button[type="submit"]');
    await page.waitForURL('**/founder', { timeout: 15000 }).catch(() => {});
    
    await checkPage(page, '/founder', 'Founder Dashboard');
    await checkPage(page, '/founder/startups', 'Founder Startups');
    await checkPage(page, '/founder/discover', 'Founder Discover');
    await checkPage(page, '/founder/matches', 'Founder Matches');
    await checkPage(page, '/founder/analytics', 'Founder Analytics');
    await checkPage(page, '/meetings', 'Founder Meetings');
    await checkPage(page, '/founder/profile', 'Founder Profile');
  });

  test('Investor Flow', async ({ page }) => {
    await page.goto(`${BASE_URL}/auth/login`);
    await page.fill('input[type="email"]', 'investor@test.com');
    await page.fill('input[type="password"]', 'password123');
    await page.click('button[type="submit"]');
    await page.waitForURL('**/investor', { timeout: 15000 }).catch(() => {});
    
    await checkPage(page, '/investor', 'Investor Dashboard');
    await checkPage(page, '/investor/discover', 'Investor Discover Startups');
    await checkPage(page, '/investor/matches', 'Investor Matches');
    await checkPage(page, '/investor/deals', 'Investor Deals');
    await checkPage(page, '/investor/analytics', 'Investor Analytics');
    await checkPage(page, '/investor/profile', 'Investor Profile');
  });

  test('Admin Flow', async ({ page }) => {
    await page.goto(`${BASE_URL}/auth/login`);
    await page.fill('input[type="email"]', 'admin@investo.com');
    await page.fill('input[type="password"]', 'password123');
    await page.click('button[type="submit"]');
    await page.waitForURL('**/admin', { timeout: 15000 }).catch(() => {});
    
    await checkPage(page, '/admin', 'Admin Dashboard');
    await checkPage(page, '/admin/users', 'Admin Users');
    await checkPage(page, '/admin/tickets', 'Admin Tickets');
    await checkPage(page, '/admin/audit', 'Admin Audit');
    await checkPage(page, '/admin/revenue', 'Admin Revenue');
    await checkPage(page, '/admin/ops', 'Admin Ops');
  });
  
  test('Chat Flow', async ({ page }) => {
    await page.goto(`${BASE_URL}/auth/login`);
    await page.fill('input[type="email"]', 'founder@test.com');
    await page.fill('input[type="password"]', 'password123');
    await page.click('button[type="submit"]');
    await page.waitForURL('**/founder', { timeout: 15000 }).catch(() => {});
    
    await checkPage(page, '/chat', 'Chat List');
    // Try to open first conversation
    try {
      await page.goto(`${BASE_URL}/chat`, { waitUntil: 'networkidle' });
      const firstConv = await page.$('a[href^="/chat/"]');
      if (firstConv) {
         const href = await firstConv.getAttribute('href');
         await checkPage(page, href, 'Chat Open');
      } else {
         RESULTS.push({ Flow: 'Chat Open', Path: '/chat/*', Pass: 'FAIL', Errors: 'No conversations found to open', Screenshot: '' });
      }
    } catch(e) {
      // ignore
    }
  });

  test.afterAll(() => {
    fs.writeFileSync(path.join(ARTIFACT_DIR, 'results.json'), JSON.stringify(RESULTS, null, 2));
    console.log("\\n=== QA RESULTS ===");
    console.table(RESULTS);
  });
});
