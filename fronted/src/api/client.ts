import { mockApi } from './mockApi';

// In the future, this file will use axios to make real HTTP requests.
// For now, it proxies to the mock API to unblock UI development.

export const apiClient = {
  startInterview: mockApi.startInterview,
  submitAnswer: mockApi.submitAnswer,
  getHint: mockApi.getHint,
  getFeedback: mockApi.getFeedback,
  abortInterview: mockApi.abortInterview,
};
