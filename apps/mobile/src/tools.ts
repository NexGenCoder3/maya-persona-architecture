export interface SearchResult {
  title: string;
  url: string;
}

export interface WeatherResult {
  city: string;
  country?: string;
  temperatureC: number;
  apparentTemperatureC?: number;
  conditions: string;
  updatedAt: string;
  source: 'Open-Meteo';
}

export interface ReadOnlyTools {
  search(query: string): Promise<SearchResult[]>;
  weather(city: string): Promise<WeatherResult>;
}

export class ToolInputError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'ToolInputError';
  }
}

const WEATHER_CODES: Record<number, string> = {
  0: 'Clear', 1: 'Mainly clear', 2: 'Partly cloudy', 3: 'Overcast',
  45: 'Fog', 48: 'Depositing rime fog', 51: 'Light drizzle', 53: 'Drizzle',
  55: 'Dense drizzle', 56: 'Freezing drizzle', 57: 'Dense freezing drizzle',
  61: 'Light rain', 63: 'Rain', 65: 'Heavy rain', 66: 'Freezing rain',
  67: 'Heavy freezing rain', 71: 'Light snow', 73: 'Snow', 75: 'Heavy snow',
  77: 'Snow grains', 80: 'Rain showers', 81: 'Rain showers', 82: 'Heavy rain showers',
  85: 'Snow showers', 86: 'Heavy snow showers', 95: 'Thunderstorm',
  96: 'Thunderstorm with hail', 99: 'Thunderstorm with heavy hail',
};

export function validateSearchQuery(raw: string): string {
  const query = raw.trim();
  if (query.length < 2 || query.length > 200 || /[\u0000-\u001f\u007f]/u.test(query)) {
    throw new ToolInputError('Enter a search query between 2 and 200 characters.');
  }
  return query;
}

export function validateCity(raw: string): string {
  const city = raw.trim();
  if (
    city.length < 2 || city.length > 80 ||
    !/^[\p{L}\p{M}][\p{L}\p{M}\s.'’\-]*$/u.test(city)
  ) {
    throw new ToolInputError('Enter a city name using letters, spaces, apostrophes, or hyphens.');
  }
  return city;
}

function decodeHtml(value: string): string {
  return value
    .replace(/&amp;/gi, '&')
    .replace(/&quot;/gi, '"')
    .replace(/&#39;|&apos;/gi, "'")
    .replace(/&lt;/gi, '<')
    .replace(/&gt;/gi, '>')
    .replace(/&#(\d+);/g, (_, code: string) => {
      const codePoint = Number(code);
      const isScalar = Number.isInteger(codePoint) && codePoint >= 0 && codePoint <= 0x10ffff &&
        !(codePoint >= 0xd800 && codePoint <= 0xdfff);
      return isScalar ? String.fromCodePoint(codePoint) : '\uFFFD';
    })
    .replace(/<[^>]*>/g, '')
    .trim();
}

function safeSearchUrl(rawHref: string): string | undefined {
  try {
    const href = decodeHtml(rawHref);
    const parsed = new URL(href, 'https://html.duckduckgo.com');
    const destination = parsed.searchParams.get('uddg') || parsed.href;
    const url = new URL(destination);
    return url.protocol === 'https:' || url.protocol === 'http:' ? url.href : undefined;
  } catch {
    return undefined;
  }
}

export async function searchPublicWeb(
  rawQuery: string,
  fetcher: typeof fetch = fetch,
): Promise<SearchResult[]> {
  const query = validateSearchQuery(rawQuery);
  let response: Response;
  try {
    response = await fetcher(`https://html.duckduckgo.com/html/?q=${encodeURIComponent(query)}`, {
      headers: { Accept: 'text/html' },
    });
  } catch {
    throw new Error('Public web search is unavailable while offline.');
  }
  if (!response.ok) throw new Error('Public web search could not be completed.');
  const html = await response.text();
  const anchorPattern = /<a\b(?=[^>]*\bclass=["'][^"']*\bresult__a\b)[^>]*\bhref=["']([^"']+)["'][^>]*>([\s\S]*?)<\/a>/gi;
  const results: SearchResult[] = [];
  let match: RegExpExecArray | null;
  while ((match = anchorPattern.exec(html)) && results.length < 5) {
    const url = safeSearchUrl(match[1]);
    const title = decodeHtml(match[2]);
    if (url && title) results.push({ title, url });
  }
  return results;
}

export async function getCityWeather(
  rawCity: string,
  fetcher: typeof fetch = fetch,
): Promise<WeatherResult> {
  const city = validateCity(rawCity);
  const geocodeUrl = new URL('https://geocoding-api.open-meteo.com/v1/search');
  geocodeUrl.searchParams.set('name', city);
  geocodeUrl.searchParams.set('count', '5');
  geocodeUrl.searchParams.set('language', 'en');
  geocodeUrl.searchParams.set('format', 'json');
  let geocodeResponse: Response;
  try {
    geocodeResponse = await fetcher(geocodeUrl.href, { headers: { Accept: 'application/json' } });
  } catch {
    throw new Error('Weather lookup is unavailable while offline.');
  }
  if (!geocodeResponse.ok) throw new Error('The city could not be looked up.');
  const geocode = await geocodeResponse.json() as {
    results?: Array<{ name?: unknown; country?: unknown; latitude?: unknown; longitude?: unknown; timezone?: unknown }>;
  };
  const place = geocode.results?.find((entry) =>
    typeof entry.name === 'string' &&
    typeof entry.latitude === 'number' && Number.isFinite(entry.latitude) &&
    typeof entry.longitude === 'number' && Number.isFinite(entry.longitude)
  );
  if (!place || typeof place.name !== 'string' || typeof place.latitude !== 'number' || typeof place.longitude !== 'number') {
    throw new ToolInputError('No matching city was found. Check the spelling and try again.');
  }
  const weatherUrl = new URL('https://api.open-meteo.com/v1/forecast');
  weatherUrl.searchParams.set('latitude', String(place.latitude));
  weatherUrl.searchParams.set('longitude', String(place.longitude));
  weatherUrl.searchParams.set('current', 'temperature_2m,apparent_temperature,weather_code');
  weatherUrl.searchParams.set('timezone', typeof place.timezone === 'string' ? place.timezone : 'auto');
  let weatherResponse: Response;
  try {
    weatherResponse = await fetcher(weatherUrl.href, { headers: { Accept: 'application/json' } });
  } catch {
    throw new Error('Weather lookup is unavailable while offline.');
  }
  if (!weatherResponse.ok) throw new Error('Current weather could not be loaded.');
  const weather = await weatherResponse.json() as {
    current?: { temperature_2m?: unknown; apparent_temperature?: unknown; weather_code?: unknown; time?: unknown };
  };
  const current = weather.current;
  if (
    !current || typeof current.temperature_2m !== 'number' || !Number.isFinite(current.temperature_2m) ||
    typeof current.weather_code !== 'number' || typeof current.time !== 'string' || !current.time
  ) {
    throw new Error('The weather service returned incomplete current conditions.');
  }
  return {
    city: place.name,
    ...(typeof place.country === 'string' ? { country: place.country } : {}),
    temperatureC: current.temperature_2m,
    ...(typeof current.apparent_temperature === 'number' && Number.isFinite(current.apparent_temperature)
      ? { apparentTemperatureC: current.apparent_temperature }
      : {}),
    conditions: WEATHER_CODES[current.weather_code] ?? 'Current conditions',
    updatedAt: current.time,
    source: 'Open-Meteo',
  };
}

export const publicReadOnlyTools: ReadOnlyTools = {
  search: searchPublicWeb,
  weather: getCityWeather,
};
