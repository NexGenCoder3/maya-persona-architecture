import { createHttpReporter, createHttpTurnCore, OfflineError, ReportRequest, TurnRequest } from '../src/core';

function response(payload: unknown, ok = true): Response {
  return {
    ok,
    status: ok ? 200 : 502,
    json: async () => payload,
  } as Response;
}

function mockFetch() {
  const mock = jest.fn<Promise<Response>, [RequestInfo | URL, RequestInit?]>();
  return { mock, fetcher: mock as unknown as typeof fetch };
}

describe('shared core and report HTTP adapters', () => {
  it('posts ordered history to the existing shared completion endpoint with session identity and no model secrets', async () => {
    const { mock, fetcher } = mockFetch();
    mock.mockResolvedValue(response({ choices: [{ message: { content: 'Shared-core reply.' } }] }));
    const core = createHttpTurnCore('http://127.0.0.1:5000/', fetcher);
    const request: TurnRequest = {
      sessionId: 'session-abc123',
      requestId: 'assistant-abc123',
      messages: [
        { role: 'user', content: 'First message' },
        { role: 'assistant', content: 'First reply' },
        { role: 'user', content: 'Second message' },
      ],
    };
    await expect(core.complete(request)).resolves.toBe('Shared-core reply.');
    expect(mock).toHaveBeenCalledTimes(1);
    const [url, options] = mock.mock.calls[0];
    expect(url).toBe('http://127.0.0.1:5000/v1/chat/completions');
    expect(options?.headers).toEqual({
      'Content-Type': 'application/json',
      'X-Maya-Session-ID': request.sessionId,
      'X-Maya-Request-ID': request.requestId,
    });
    expect(JSON.parse(String(options?.body))).toEqual({ stream: false, messages: request.messages });
    expect(String(options?.body)).not.toMatch(/api[_-]?key|authorization|system_prompt/i);
  });

  it('does not call a model endpoint when no API origin is configured', async () => {
    const { mock, fetcher } = mockFetch();
    const core = createHttpTurnCore('', fetcher);
    await expect(core.complete({ sessionId: 's1', requestId: 'r1', messages: [{ role: 'user', content: 'Hi' }] })).rejects.toBeInstanceOf(OfflineError);
    expect(mock).not.toHaveBeenCalled();
  });

  it('submits only the explicitly reported assistant reply to the report endpoint', async () => {
    const { mock, fetcher } = mockFetch();
    mock.mockResolvedValue(response({ accepted: true, duplicate: false }));
    const reporter = createHttpReporter('http://127.0.0.1:5000', fetcher);
    const report: ReportRequest = {
      reportId: 'report-assistant-abc123',
      sessionId: 'session-abc123',
      messageId: 'assistant-abc123',
      category: 'offensive_output',
      content: 'Only the flagged assistant reply.',
    };
    await expect(reporter.submit(report)).resolves.toBeUndefined();
    expect(mock).toHaveBeenCalledTimes(1);
    const [url, options] = mock.mock.calls[0];
    expect(url).toBe('http://127.0.0.1:5000/v1/reports');
    expect(JSON.parse(String(options?.body))).toEqual({
      report_id: report.reportId,
      session_id: report.sessionId,
      message_id: report.messageId,
      category: report.category,
      content: report.content,
    });
  });
});
