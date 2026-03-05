export interface ApiError {
  code: string
  message: string
  details?: Record<string, unknown>
}

export interface ApiEnvelope<T> {
  request_id: string
  data: T
  error: ApiError | null
}
