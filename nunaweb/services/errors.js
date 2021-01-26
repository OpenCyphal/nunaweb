export class APIError extends Error {
  constructor(message, statusCode, ...params) {
    // Pass remaining arguments (including vendor specific ones) to parent constructor
    super(message, ...params);

    // Maintains proper stack trace for where our error was thrown (only available on V8)
    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, APIError);
    }

    this.name = 'APIError';
    this.statusCode = statusCode;
  }
}

export function handleErrors(e) {
  // Error handling
  if (e instanceof APIError) {
    // Handle error codes
    switch (e.status) {
      case 400: {
        this.loadingStatus = 'FAILURE';
        this.loadingMessage = 'One or more fields are missing or incorrect.';
        break;
      }
      case 413: {
        this.loadingStatus = 'FAILURE';
        this.loadingMessage = 'Namespace upload size too large.';
        break;
      }
      case 500: {
        this.loadingStatus = 'FAILURE';
        this.loadingMessage = 'Backend encountered an unexpected error';
        break;
      }
      default: {
        this.loadingStatus = 'FAILURE';
        this.loadingMessage = 'Unknown failure during generation.';
        break;
      }
    }
  } else {
    // Probably a connect failure
    this.loadingStatus = 'FAILURE';
    this.loadingMessage = 'Could not contact backend. Please try again later. Message: ' + e.message;
  }
}
