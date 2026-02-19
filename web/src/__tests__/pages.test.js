import { describe, it, expect, vi } from 'vitest';
import React from 'react';

// Lightweight render check without full DOM — validates component exports and structure
describe('Page Components', () => {
  it('App.jsx exports a default component', async () => {
    // Verify module structure
    const mod = await import('../App.jsx');
    expect(mod.default).toBeDefined();
    expect(typeof mod.default).toBe('function');
  });

  it('Settings page exports default component', async () => {
    const mod = await import('../pages/Settings.jsx');
    expect(mod.default).toBeDefined();
    expect(typeof mod.default).toBe('function');
  });

  it('Dashboard page exports default component', async () => {
    const mod = await import('../pages/Dashboard.jsx');
    expect(mod.default).toBeDefined();
    expect(typeof mod.default).toBe('function');
  });

  it('Scan page exports default component', async () => {
    const mod = await import('../pages/Scan.jsx');
    expect(mod.default).toBeDefined();
    expect(typeof mod.default).toBe('function');
  });

  it('Results page exports default component', async () => {
    const mod = await import('../pages/Results.jsx');
    expect(mod.default).toBeDefined();
    expect(typeof mod.default).toBe('function');
  });

  it('ScanHistory page exports default component', async () => {
    const mod = await import('../pages/ScanHistory.jsx');
    expect(mod.default).toBeDefined();
    expect(typeof mod.default).toBe('function');
  });

  it('Feedback page exports default component', async () => {
    const mod = await import('../pages/Feedback.jsx');
    expect(mod.default).toBeDefined();
    expect(typeof mod.default).toBe('function');
  });

  it('ModelStatus page exports default component', async () => {
    const mod = await import('../pages/ModelStatus.jsx');
    expect(mod.default).toBeDefined();
    expect(typeof mod.default).toBe('function');
  });

  it('LearningIntelligence page exports default component', async () => {
    const mod = await import('../pages/LearningIntelligence.jsx');
    expect(mod.default).toBeDefined();
    expect(typeof mod.default).toBe('function');
  });

  it('NotFound page exports default component', async () => {
    const mod = await import('../pages/NotFound.jsx');
    expect(mod.default).toBeDefined();
    expect(typeof mod.default).toBe('function');
  });

  it('Layout component exports default', async () => {
    const mod = await import('../components/Layout.jsx');
    expect(mod.default).toBeDefined();
    expect(typeof mod.default).toBe('function');
  });

  it('ErrorBoundary component exports default', async () => {
    const mod = await import('../components/ErrorBoundary.jsx');
    expect(mod.default).toBeDefined();
  });
});

describe('Route Configuration', () => {
  it('App defines all expected routes', async () => {
    // Read source to validate route strings
    const appSource = (await import('../App.jsx?raw')).default;
    
    const expectedRoutes = [
      '/', '/dashboard', '/learning', '/results', '/history',
      '/feedback', '/model-status', '/settings', '*'
    ];
    
    for (const route of expectedRoutes) {
      expect(appSource).toContain(`path="${route}"`);
    }
  });

  it('Layout defines navigation items matching routes', async () => {
    const layoutSource = (await import('../components/Layout.jsx?raw')).default;
    
    const navItems = ['Scan', 'Dashboard', 'Learning', 'History', 'Feedback', 'Model Status', 'Settings'];
    for (const item of navItems) {
      expect(layoutSource).toContain(item);
    }
  });
});
