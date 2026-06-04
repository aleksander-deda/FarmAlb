/**
 * Extract error message from various error formats
 */
export function getErrorMessage(error) {
  // If error has a data object with message (from our interceptor)
  if (error?.data?.message) {
    return error.data.message
  }

  // If error has response with data.message
  if (error?.response?.data?.message) {
    return error.response.data.message
  }

  // If error message is directly available
  if (error?.message) {
    return error.message
  }

  // Default fallback
  return 'Something went wrong. Please try again.'
}

/**
 * Extract error details (for field-level validation errors)
 */
export function getErrorDetails(error) {
  // Check for error details in ApiResponse structure
  if (error?.data?.errors) {
    return error.data.errors
  }

  if (error?.response?.data?.errors) {
    return error.response.data.errors
  }

  return {}
}

/**
 * Handle API error gracefully
 */
export function handleApiError(error, options = {}) {
  const { showAlert = true, callback } = options

  const message = getErrorMessage(error)
  const details = getErrorDetails(error)

  if (callback) {
    callback(message, details)
  }

  return { message, details, error }
}
