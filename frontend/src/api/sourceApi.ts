import apiClient from './client';
import type { SourcePathRequest, SourceCheckResponse, ScanResult, LogSearchParams, LogSearchResponse } from '../types/api';

export async function checkSourceDirectory(
  path: string
): Promise<SourceCheckResponse> {
  const response = await apiClient.post<SourceCheckResponse>(
    '/source/check',
    { path } as SourcePathRequest
  );
  return response.data;
}

export async function scanSourceDirectory(
  path: string
): Promise<ScanResult> {
  const response = await apiClient.post<ScanResult>('/source/scan', {
    path,
  } as SourcePathRequest);
  return response.data;
}

export async function searchLogContent(
  params: LogSearchParams
): Promise<LogSearchResponse> {
  const response = await apiClient.post<LogSearchResponse>('/source/search', params);
  return response.data;
}

export async function uploadFiles(
  files: File[]
): Promise<{ path: string; file_count: number; relative_path: string }> {
  const formData = new FormData();
  for (const file of files) {
    formData.append('files', file);
  }
  const response = await apiClient.post('/source/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data as { path: string; file_count: number; relative_path: string };
}
