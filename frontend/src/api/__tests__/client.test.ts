import { describe, it, expect } from 'vitest';
import apiClient from '../client';

describe('apiClient', () => {
  it('creates axios instance with correct baseURL', () => {
    expect(apiClient.defaults.baseURL).toBe('/api');
  });

  it('creates axios instance with correct timeout', () => {
    expect(apiClient.defaults.timeout).toBe(30000);
  });

  it('has request interceptor registered', () => {
    expect(apiClient.interceptors.request.handlers.length).toBeGreaterThan(0);
  });

  it('has response interceptor registered', () => {
    expect(apiClient.interceptors.response.handlers.length).toBeGreaterThan(0);
  });
});
