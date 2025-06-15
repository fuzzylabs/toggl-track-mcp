import { RateLimiter } from '../src/utils/rate-limiter.js';

describe('RateLimiter', () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('should allow requests within rate limit', async () => {
    const limiter = new RateLimiter(1, 3);
    const start = Date.now();

    await limiter.waitForToken();
    await limiter.waitForToken();
    await limiter.waitForToken();

    const elapsed = Date.now() - start;
    expect(elapsed).toBeLessThan(100);
  });

  it('should delay requests when rate limit exceeded', async () => {
    const limiter = new RateLimiter(1, 2);
    
    const times: number[] = [];
    
    const start = Date.now();
    times.push(Date.now() - start);
    
    await limiter.waitForToken();
    times.push(Date.now() - start);
    
    await limiter.waitForToken();
    times.push(Date.now() - start);
    
    const waitPromise = limiter.waitForToken();
    jest.advanceTimersByTime(1000);
    await waitPromise;
    times.push(Date.now() - start);

    expect(times[0]).toBe(0);
    expect(times[1]).toBeLessThan(50);
    expect(times[2]).toBeLessThan(50);
    expect(times[3]).toBeGreaterThanOrEqual(1000);
  });

  it('should refill tokens over time', async () => {
    const limiter = new RateLimiter(2, 1);

    await limiter.waitForToken();
    expect(limiter.getAvailableTokens()).toBeLessThan(1);

    jest.advanceTimersByTime(500);
    expect(limiter.getAvailableTokens()).toBeCloseTo(1, 1);

    jest.advanceTimersByTime(500);
    expect(limiter.getAvailableTokens()).toBe(1);
  });
});