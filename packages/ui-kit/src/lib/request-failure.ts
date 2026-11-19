/** Why a request failed, in the terms a person can act on. */
export type RequestFailure = 'unreachable' | 'signed-out' | 'other';

const MESSAGES: Record<RequestFailure, string> = {
  unreachable:
    'The server could not be reached. Check your connection, then retry.',
  'signed-out': 'Your sign-in has expired. Sign in again, then retry.',
  other: 'Something went wrong. Try again in a moment.',
};

/** The plain-language message any screen shows for a failed request, with a way forward. */
export function requestFailureMessage(failure: RequestFailure): string {
  return MESSAGES[failure];
}
