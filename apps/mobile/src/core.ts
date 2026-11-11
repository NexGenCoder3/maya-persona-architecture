export type ChatRole = 'user' | 'assistant';

export interface ChatLine {
  role: ChatRole;
  content: string;
}

export interface TurnRequest {
  sessionId: string;
  requestId: string;
  messages: ChatLine[];
}

export interface TurnCore {
  complete(request: TurnRequest): Promise<string>;
}

export interface ReportRequest {
  reportId: string;
  sessionId: string;
  messageId: string;
  category: 'offensive_output';
  content: string;
}

export interface Reporter {
  submit(request: ReportRequest): Promise<void>;
}

export class OfflineError extends Error {
  readonly code = 'offline';

  constructor(message = 'The Maya API is not reachable right now.') {
    super(message);
    this.name = 'OfflineError';
  }
}

export class CoreRequestError extends Error {
  readonly code = 'request_error';

  constructor(message: string) {
    super(message);
    this.name = 'CoreRequestError';
  }
}

function cleanBaseUrl(baseUrl: string): string {
  return baseUrl.trim().replace(/\/+$/, '');
}

async function readJson(response: Response): Promise<unknown> {
  try {
    return await response.json();
  } catch {
    throw new CoreRequestError('The Maya API returned an unreadable response.');
  }
}

export function createHttpTurnCore(
  baseUrl: string,
  fetcher: typeof fetch = fetch,
): TurnCore {
  return {
    async complete(request) {
      const base = cleanBaseUrl(baseUrl);
      if (!base) throw new OfflineError('Connect a Maya API endpoint to chat.');
      let response: Response;
      try {
        response = await fetcher(`${base}/v1/chat/completions`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-Maya-Session-ID': request.sessionId,
            'X-Maya-Request-ID': request.requestId,
          },
          body: JSON.stringify({
            stream: false,
            messages: request.messages,
          }),
        });
      } catch {
        throw new OfflineError();
      }
      const payload = await readJson(response) as {
        choices?: Array<{ message?: { content?: unknown } }>;
        error?: { message?: unknown };
      };
      if (!response.ok) {
        const message = typeof payload?.error?.message === 'string'
          ? payload.error.message
          : 'The Maya API could not complete that turn.';
        throw new CoreRequestError(message);
      }
      const content = payload?.choices?.[0]?.message?.content;
      if (typeof content !== 'string' || !content.trim()) {
        throw new CoreRequestError('The Maya API returned no assistant text.');
      }
      return content;
    },
  };
}

export function createHttpReporter(
  baseUrl: string,
  fetcher: typeof fetch = fetch,
): Reporter {
  return {
    async submit(request) {
      const base = cleanBaseUrl(baseUrl);
      if (!base) throw new OfflineError('Reporting is unavailable while offline.');
      let response: Response;
      try {
        response = await fetcher(`${base}/v1/reports`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            report_id: request.reportId,
            session_id: request.sessionId,
            message_id: request.messageId,
            category: request.category,
            content: request.content,
          }),
        });
      } catch {
        throw new OfflineError('Reporting is unavailable while offline.');
      }
      const payload = await readJson(response) as { accepted?: unknown; error?: { message?: unknown } };
      if (!response.ok || payload?.accepted !== true) {
        const message = typeof payload?.error?.message === 'string'
          ? payload.error.message
          : 'The report could not be submitted.';
        throw new CoreRequestError(message);
      }
    },
  };
}
