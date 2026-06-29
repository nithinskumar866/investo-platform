import { test, expect } from '@playwright/test';
import fs from 'fs';

const BASE_URL = 'http://localhost:3000';
const results: any[] = [];

test.use({ actionTimeout: 60000, navigationTimeout: 60000 });

async function checkPage(page: any, role: string, name: string, path: string) {
  console.log(`Checking ${name} at ${path}`);
  let currentErrors: string[] = [];
  let currentApiFailures: string[] = [];
  
  const errHandler = (err: any) => currentErrors.push(err.message);
  const consoleHandler = (msg: any) => {
    if (msg.type() === 'error' && !msg.text().includes('favicon') && !msg.text().includes('Warning:')) {
      currentErrors.push(msg.text());
    }
  };
  const respHandler = (resp: any) => {
    if (!resp.ok() && resp.url().includes('/api/') && resp.request().method() === 'GET') {
      currentApiFailures.push(`${resp.status()} ${resp.url()}`);
    }
  };

  page.on('pageerror', errHandler);
  page.on('console', consoleHandler);
  page.on('response', respHandler);

  try {
    await page.goto(`${BASE_URL}${path}`, { waitUntil: 'networkidle', timeout: 60000 });
    await page.waitForTimeout(2000);
    const content = await page.content();
    
    const emptyState = content.includes('Application Error') || 
                       content.includes('placeholder') || 
                       content.includes('No data') ||
                       content.includes('Chart placeholder');
                       
    let navIssues = 'None';
    if(content.includes('404') || content.includes('This page could not be found')) {
        navIssues = '404 Not Found';
    }
    
    let pass = currentErrors.length === 0 && currentApiFailures.length === 0 && !emptyState && navIssues === 'None' ? 'PASS' : 'FAIL';
    
    results.push({
      Role: role,
      Page: name,
      Status: pass,
      Exceptions: currentErrors.join(' | ') || 'None',
      APIFailures: currentApiFailures.join(' | ') || 'None',
      EmptyStates: emptyState ? 'Detected' : 'None',
      NavigationIssues: navIssues
    });
  } catch(e: any) {
    results.push({
      Role: role,
      Page: name,
      Status: 'FAIL',
      Exceptions: e.message,
      APIFailures: 'N/A',
      EmptyStates: 'N/A',
      NavigationIssues: 'Timeout/Crash'
    });
  }
  
  page.off('pageerror', errHandler);
  page.off('console', consoleHandler);
  page.off('response', respHandler);
}

test.describe.serial('UI Audit', () => {
  test('Founder Pages', async ({ page }) => {
    test.setTimeout(240000);
    await page.goto(`${BASE_URL}/auth/login`);
    await page.fill('input[type="email"]', 'founder@investo.com');
    await page.fill('input[type="password"]', 'founder123');
    await page.click('button[type="submit"]');
    await page.waitForURL(`**/founder`, { timeout: 60000 }).catch(() => {});
    
    await checkPage(page, 'Founder', 'Dashboard', '/founder');
    await checkPage(page, 'Founder', 'Startups', '/founder/startups');
    await checkPage(page, 'Founder', 'Discover', '/founder/discover');
    await checkPage(page, 'Founder', 'Meetings', '/meetings');
    await checkPage(page, 'Founder', 'Matches', '/founder/matches');
    await checkPage(page, 'Chat', 'Conversation list', '/chat');
    
    try {
      await page.goto(`${BASE_URL}/chat`, { waitUntil: 'networkidle', timeout: 60000 });
      const firstConv = await page.$('a[href^="/chat/"]');
      if (firstConv) {
         const href = await firstConv.getAttribute('href');
         if (href) await checkPage(page, 'Chat', 'Conversation view', href);
         const msgInput = await page.$('input[placeholder*="Type"]');
         results.push({
            Role: 'Chat', Page: 'Send message', Status: msgInput ? 'PASS' : 'FAIL',
            Exceptions: 'None', APIFailures: 'None', EmptyStates: 'None', NavigationIssues: msgInput ? 'None' : 'Input missing'
         });
      } else {
         results.push({ Role: 'Chat', Page: 'Conversation view', Status: 'FAIL', Exceptions: 'No conversation found', APIFailures: 'None', EmptyStates: 'Detected', NavigationIssues: 'None' });
         results.push({ Role: 'Chat', Page: 'Send message', Status: 'FAIL', Exceptions: 'No conversation found', APIFailures: 'None', EmptyStates: 'Detected', NavigationIssues: 'None' });
      }
    } catch(e) {}
  });

  test('Investor Pages', async ({ page }) => {
    test.setTimeout(180000);
    await page.goto(`${BASE_URL}/auth/login`);
    await page.fill('input[type="email"]', 'investor@investo.com');
    await page.fill('input[type="password"]', 'investor123');
    await page.click('button[type="submit"]');
    await page.waitForURL(`**/investor`, { timeout: 60000 }).catch(() => {});
    
    await checkPage(page, 'Investor', 'Dashboard', '/investor');
    await checkPage(page, 'Investor', 'Deals', '/investor/deals');
    await checkPage(page, 'Investor', 'Analytics', '/investor/analytics');
    await checkPage(page, 'Investor', 'Discover', '/investor/discover');
  });

  test('Admin Pages', async ({ page }) => {
    test.setTimeout(180000);
    await page.goto(`${BASE_URL}/auth/login`);
    await page.fill('input[type="email"]', 'admin@investo.com');
    await page.fill('input[type="password"]', 'admin123');
    await page.click('button[type="submit"]');
    await page.waitForURL(`**/admin`, { timeout: 60000 }).catch(() => {});
    
    await checkPage(page, 'Admin', 'Users', '/admin/users');
    await checkPage(page, 'Admin', 'Tickets', '/admin/tickets');
    await checkPage(page, 'Admin', 'Audit', '/admin/audit');
    await checkPage(page, 'Admin', 'Revenue', '/admin/revenue');
    await checkPage(page, 'Admin', 'Ops', '/admin/ops');
  });

  test.afterAll(() => {
    fs.writeFileSync('C:\\Users\\nithi\\.gemini\\antigravity-ide\\brain\\fd444762-25ce-4671-ac6b-7e9ab7e0e2fd\\scratch\\audit_results.json', JSON.stringify(results, null, 2));
    console.log('JSON_RESULT_START', JSON.stringify(results), 'JSON_RESULT_END');
  });
});
