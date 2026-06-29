import { test, expect, request } from '@playwright/test';

const BASE_URL = 'http://localhost:3000';
const API_URL = 'http://localhost:8000/api/v1';

test.describe.serial('E2E User Journey (Entrepreneur & Investor)', () => {
  const runId = Date.now();
  const entrepreneurEmail = `nathan_e2e_${runId}@test.com`;
  const investorEmail = `sandhya_e2e_${runId}@test.com`;
  
  let entrepreneurToken = '';
  let investorToken = '';
  let entrepreneurId = 0;
  let investorId = 0;
  let startupId = 0;
  let conversationId = 0;

  test.setTimeout(60000); // Increase timeout to 60s for all tests in this describe block

  test('1. Register Entrepreneur (Nathan)', async ({ page }) => {
    await page.goto(`${BASE_URL}/auth/register`);
    await page.fill('input[name="first_name"]', 'Nathan');
    await page.fill('input[name="last_name"]', 'Founder');
    await page.fill('input[name="email"]', entrepreneurEmail);
    await page.fill('input[name="password"]', 'StrongPass123!');
    await page.fill('input[name="confirm_password"]', 'StrongPass123!');
    
    await page.getByText('I have a startup').click();
    
    // Listen for the register response
    const [response] = await Promise.all([
      page.waitForResponse(res => res.url().includes('/auth/register/') && res.request().method() === 'POST'),
      page.click('button[type="submit"]')
    ]);
    
    const body = await response.json();
    console.log("Register response:", body);
    
    await page.waitForURL('**/auth/login', { timeout: 15000 });
    expect(page.url()).toContain('/auth/login');
  });

  test('2. Seed Entrepreneur Startup (API Fallback) & UI Login', async ({ page, request }) => {
    const loginRes = await request.post(`${API_URL}/auth/login/`, {
      data: { email: entrepreneurEmail, password: 'StrongPass123!' }
    });
    expect(loginRes.ok()).toBeTruthy();
    const loginData = await loginRes.json();
    entrepreneurToken = loginData.data.tokens.access;
    entrepreneurId = loginData.data.user.id;

    // Seed Startup Profile via API
    const startupRes = await request.post(`${API_URL}/startups/`, {
      headers: { Authorization: `Bearer ${entrepreneurToken}` },
      data: {
        name: `Nathan AI Startup ${runId}`,
        tagline: 'Revolutionizing AI',
        description: 'An end-to-end AI platform for investors.',
        industry: 'ai_ml',
        stage: 'pre_seed',
        location: 'San Francisco, CA',
        funding_goal: 1000000,
        equity_offered: 10
      }
    });
    const startupData = await startupRes.json();
    console.log("Startup creation response:", startupData);
    if (!startupRes.ok()) {
      console.log("Startup creation failed:", startupData);
    }
    expect(startupRes.ok()).toBeTruthy();
    startupId = startupData.data ? startupData.data.id : startupData.id;

    // Publish the startup so it's visible
    const publishRes = await request.post(`${API_URL}/startups/${startupId}/publish/`, {
      headers: { Authorization: `Bearer ${entrepreneurToken}` }
    });
    const publishData = await publishRes.json();
    console.log("Startup publish response:", publishData);

    // Verify UI Login
    await page.goto(`${BASE_URL}/auth/login`);
    await page.fill('input[name="email"]', entrepreneurEmail);
    await page.fill('input[name="password"]', 'StrongPass123!');
    await page.click('button[type="submit"]');
    await page.waitForURL('**/founder', { timeout: 15000 });
    
    // Check Dashboard/Startups
    await page.goto(`${BASE_URL}/founder/startups`);
    await expect(page.getByText(`Nathan AI Startup ${runId}`)).toBeVisible();
  });

  test('3. Register Investor (Sandhya)', async ({ page }) => {
    await page.goto(`${BASE_URL}/auth/register`);
    await page.fill('input[name="first_name"]', 'Sandhya');
    await page.fill('input[name="last_name"]', 'Investor');
    await page.fill('input[name="email"]', investorEmail);
    await page.fill('input[name="password"]', 'StrongPass123!');
    await page.fill('input[name="confirm_password"]', 'StrongPass123!');
    
    await page.getByText('I want to invest').click();
    await page.click('button[type="submit"]');
    
    await page.waitForURL('**/auth/login', { timeout: 15000 });
  });

  test('4. Seed Investor Profile (API Fallback) & UI Login', async ({ page, request }) => {
    const loginRes = await request.post(`${API_URL}/auth/login/`, {
      data: { email: investorEmail, password: 'StrongPass123!' }
    });
    expect(loginRes.ok()).toBeTruthy();
    const loginData = await loginRes.json();
    investorToken = loginData.data.tokens.access;
    investorId = loginData.data.user.id;
    console.log("Investor login role:", loginData.data.user.role);

    // Seed Investor Profile via API
    const profileRes = await request.patch(`${API_URL}/auth/profile/investor/`, {
      headers: { Authorization: `Bearer ${investorToken}` },
      data: {
        bio: 'Looking to invest in AI.',
        preferred_industries: ['ai_ml'],
        preferred_stages: ['pre_seed', 'seed'],
        ticket_size_min: 50000,
        ticket_size_max: 500000
      }
    });
    const profileData = await profileRes.json();
    if (!profileRes.ok()) {
      console.log("Investor profile creation failed:", profileData);
    }
    expect(profileRes.ok()).toBeTruthy();

    // Seed Investor Matching Preferences via API
    const prefRes = await request.patch(`${API_URL}/matching/preferences/`, {
      headers: { Authorization: `Bearer ${investorToken}` },
      data: {
        preferred_industries: ['ai_ml'],
        preferred_stages: ['pre_seed', 'seed'],
        min_ticket_size: 50000,
        max_ticket_size: 500000,
        investment_focus: 'AI tools and SaaS'
      }
    });
    const prefData = await prefRes.json();
    if (!prefRes.ok()) {
      console.log("Investor preference creation failed:", prefData);
    }
    expect(prefRes.ok()).toBeTruthy();

    await page.goto(`${BASE_URL}/auth/login`);
    await page.fill('input[name="email"]', investorEmail);
    await page.fill('input[name="password"]', 'StrongPass123!');
    await page.click('button[type="submit"]');
    await page.waitForURL('**/investor', { timeout: 15000 });
  });

  test('5. Investor Views Matches and Connects via Chat', async ({ page, request }) => {
    await page.goto(`${BASE_URL}/auth/login`);
    await page.fill('input[name="email"]', investorEmail);
    await page.fill('input[name="password"]', 'StrongPass123!');
    await page.click('button[type="submit"]');
    await page.waitForURL('**/investor', { timeout: 15000 });

    // Go to matches
    // Trigger match generation
    const debugRes = await request.get(`${API_URL}/matching/investor/matches/?debug=true`, {
      headers: { Authorization: `Bearer ${investorToken}` }
    });
    console.log("DEBUG MATCHES:", await debugRes.json());

    const matchesRes = await request.get(`${API_URL}/matching/investor/matches/?reload=true`, {
      headers: { Authorization: `Bearer ${investorToken}` }
    });
    const matchesData = await matchesRes.json();
    console.log("Matches generated:", JSON.stringify(matchesData, null, 2));

    await page.goto(`${BASE_URL}/investor/matches`);
    // Check if the startup appears in matches
    await expect(page.getByText(`Nathan AI Startup ${runId}`)).toBeVisible({ timeout: 10000 });

    // Click the "Message" button to auto-create conversation
    // Wait for the specific card to be visible
    const startupCard = page.locator('.space-y-3 .rounded-xl').filter({ hasText: `Nathan AI Startup ${runId}` });
    await expect(startupCard).toBeVisible({ timeout: 10000 });
    
    await startupCard.getByRole('link', { name: 'Message' }).click();

    // Wait for the URL to actually be the conversation page before extracting the ID
    await page.waitForURL(/\/chat\/\d+/);
    
    // Save conversation ID from URL
    const urlParts = page.url().split('/');
    conversationId = parseInt(urlParts[urlParts.length - 1], 10);

    // Wait for chat to load
    await expect(page.getByPlaceholder('Type a message...')).toBeVisible();

    const messageText = `Hi Nathan, Sandhya here (${runId})`;
    await page.fill('input[placeholder="Type a message..."]', messageText);
    await page.click('button[type="submit"]');

    // Message should appear
    await expect(page.getByText(messageText).first()).toBeVisible({ timeout: 15000 });
  });

  test('6. Entrepreneur receives message and replies', async ({ page }) => {
    await page.goto(`${BASE_URL}/auth/login`);
    await page.fill('input[name="email"]', entrepreneurEmail);
    await page.fill('input[name="password"]', 'StrongPass123!');
    await page.click('button[type="submit"]');
    await page.waitForURL('**/founder', { timeout: 15000 });

    await page.goto(`${BASE_URL}/chat/${conversationId}`);
    
    // Check if Sandhya's message is visible
    await expect(page.getByText(`Hi Nathan, Sandhya here (${runId})`).first()).toBeVisible({ timeout: 10000 });

    // Reply
    const replyText = `Thanks Sandhya! Looking forward to chatting. (${runId})`;
    await page.fill('input[placeholder="Type a message..."]', replyText);
    await page.click('button[type="submit"]');

    await expect(page.getByText(replyText).first()).toBeVisible({ timeout: 15000 });
  });
});
