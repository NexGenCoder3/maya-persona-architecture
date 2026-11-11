import { getCityWeather, searchPublicWeb, ToolInputError, validateCity, validateSearchQuery } from '../src/tools';

function response(body: unknown, ok = true): Response {
  return {
    ok,
    status: ok ? 200 : 503,
    json: async () => body,
    text: async () => String(body),
  } as Response;
}

function mockFetch() {
  const mock = jest.fn<Promise<Response>, [RequestInfo | URL, RequestInit?]>();
  return { mock, fetcher: mock as unknown as typeof fetch };
}

describe('public read-only tool adapters', () => {
  it('rejects malformed city and search input before making a request', async () => {
    const { mock, fetcher } = mockFetch();
    expect(() => validateCity('https://example.test')).toThrow(ToolInputError);
    expect(() => validateSearchQuery('x')).toThrow(ToolInputError);
    await expect(getCityWeather('123 !!!', fetcher)).rejects.toThrow(ToolInputError);
    await expect(searchPublicWeb('', fetcher)).rejects.toThrow(ToolInputError);
    expect(mock).not.toHaveBeenCalled();
  });

  it('returns public search source links as inert text', async () => {
    const html = '<a class="result__a" href="https://example.org/">A result &amp; an instruction</a>';
    const { mock, fetcher } = mockFetch();
    mock.mockResolvedValue(response(html));
    const results = await searchPublicWeb('public facts', fetcher);
    expect(results).toEqual([{ title: 'A result & an instruction', url: 'https://example.org/' }]);
    expect(mock).toHaveBeenCalledTimes(1);
    expect(String(mock.mock.calls[0][0])).toContain(encodeURIComponent('public facts'));
  });

  it('safely replaces an out-of-range numeric entity in untrusted result HTML', async () => {
    const { mock, fetcher } = mockFetch();
    mock.mockResolvedValue(response('<a class="result__a" href="https://example.org/">Bad entity &#99999999999;</a>'));
    await expect(searchPublicWeb('test', fetcher)).resolves.toEqual([
      { title: 'Bad entity �', url: 'https://example.org/' },
    ]);
  });

  it('looks up weather only for a valid manually entered city and returns its source timestamp', async () => {
    const { mock, fetcher } = mockFetch();
    mock
      .mockResolvedValueOnce(response({ results: [{ name: 'Accra', country: 'Ghana', latitude: 5.6, longitude: -0.2, timezone: 'Africa/Accra' }] }))
      .mockResolvedValueOnce(response({ current: { temperature_2m: 28, apparent_temperature: 30, weather_code: 2, time: '2026-11-11T12:00' } }));
    expect(validateCity(' Accra ')).toBe('Accra');
    const result = await getCityWeather('Accra', fetcher);
    expect(mock).toHaveBeenCalledTimes(2);
    expect(result).toMatchObject({ city: 'Accra', country: 'Ghana', temperatureC: 28, apparentTemperatureC: 30, conditions: 'Partly cloudy', updatedAt: '2026-11-11T12:00', source: 'Open-Meteo' });
  });

  it('fails safely when geocoding finds no place and does not request a forecast', async () => {
    const { mock, fetcher } = mockFetch();
    mock.mockResolvedValue(response({ results: [] }));
    await expect(getCityWeather('Nowhere', fetcher)).rejects.toThrow('No matching city was found');
    expect(mock).toHaveBeenCalledTimes(1);
  });
});
