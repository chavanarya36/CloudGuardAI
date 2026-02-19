import { describe, it, expect, vi, beforeEach } from 'vitest';
import axios from 'axios';

// Mock axios
vi.mock('axios', () => {
  const instance = {
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
    interceptors: {
      request: { use: vi.fn() },
      response: { use: vi.fn() },
    },
    defaults: { headers: { common: {} } },
  };
  return {
    default: { create: vi.fn(() => instance), ...instance },
    create: vi.fn(() => instance),
  };
});

describe('API Client', () => {
  let client;

  beforeEach(async () => {
    vi.resetModules();
    // Re-import to get fresh mock
    const mod = await import('../api/client.js');
    client = mod.default;
  });

  it('exports all expected API functions', async () => {
    const mod = await import('../api/client.js');
    expect(mod.scanFile).toBeDefined();
    expect(mod.getScan).toBeDefined();
    expect(mod.listScans).toBeDefined();
    expect(mod.deleteScan).toBeDefined();
    expect(mod.getScanStats).toBeDefined();
    expect(mod.getFeedbackStats).toBeDefined();
    expect(mod.submitFeedback).toBeDefined();
    expect(mod.listFeedback).toBeDefined();
    expect(mod.getModelStatus).toBeDefined();
    expect(mod.triggerRetrain).toBeDefined();
    expect(mod.listModelVersions).toBeDefined();
    expect(mod.getLearningStatus).toBeDefined();
    expect(mod.getDiscoveredPatterns).toBeDefined();
    expect(mod.getDriftStatus).toBeDefined();
    expect(mod.getRuleWeights).toBeDefined();
    expect(mod.getLearningTelemetry).toBeDefined();
    expect(mod.triggerPatternDiscovery).toBeDefined();
    expect(mod.getToken).toBeDefined();
    expect(mod.getMetrics).toBeDefined();
    expect(mod.setApiKey).toBeDefined();
    expect(mod.clearAuth).toBeDefined();
  });

  it('getScanStats calls /scans/stats', async () => {
    const mod = await import('../api/client.js');
    client.get.mockResolvedValueOnce({ data: { total_scans: 10 } });
    const result = await mod.getScanStats();
    expect(client.get).toHaveBeenCalledWith('/scans/stats');
    expect(result).toEqual({ total_scans: 10 });
  });

  it('deleteScan calls DELETE /scans/:id', async () => {
    const mod = await import('../api/client.js');
    client.delete.mockResolvedValueOnce({ data: { message: 'deleted' } });
    const result = await mod.deleteScan(5);
    expect(client.delete).toHaveBeenCalledWith('/scans/5');
    expect(result.message).toBe('deleted');
  });

  it('submitFeedback sends POST with data', async () => {
    const mod = await import('../api/client.js');
    const feedbackData = { scan_id: 1, is_correct: true };
    client.post.mockResolvedValueOnce({ data: { id: 1 } });
    const result = await mod.submitFeedback(feedbackData);
    expect(client.post).toHaveBeenCalledWith('/feedback', feedbackData);
    expect(result.id).toBe(1);
  });

  it('setApiKey persists to localStorage', async () => {
    const mod = await import('../api/client.js');
    mod.setApiKey('cg_test123');
    expect(localStorage.getItem('cg_api_key')).toBe('cg_test123');
  });

  it('clearAuth removes credentials from localStorage', async () => {
    const mod = await import('../api/client.js');
    localStorage.setItem('cg_api_key', 'test');
    localStorage.setItem('cg_jwt', 'token');
    mod.clearAuth();
    expect(localStorage.getItem('cg_api_key')).toBeNull();
    expect(localStorage.getItem('cg_jwt')).toBeNull();
  });

  it('triggerRetrain sends force and min_samples', async () => {
    const mod = await import('../api/client.js');
    client.post.mockResolvedValueOnce({ data: { job_id: 'abc' } });
    await mod.triggerRetrain(true, 50);
    expect(client.post).toHaveBeenCalledWith('/model/retrain', { force: true, min_samples: 50 });
  });

  it('getLearningTelemetry passes limit param', async () => {
    const mod = await import('../api/client.js');
    client.get.mockResolvedValueOnce({ data: { events: [] } });
    await mod.getLearningTelemetry(25);
    expect(client.get).toHaveBeenCalledWith('/learning/telemetry', { params: { limit: 25 } });
  });
});
