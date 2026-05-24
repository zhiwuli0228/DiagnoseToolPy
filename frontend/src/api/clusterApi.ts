import apiClient from './client';
import type { ClusterResponse, ClusterStatusResponse, CachedLogEntry } from '../types/api';

export async function createClusterTask(
  sourcePath: string
): Promise<ClusterResponse> {
  const response = await apiClient.post<ClusterResponse>('/cluster', {
    source_path: sourcePath,
  });
  return response.data;
}

export async function pollClusterTask(
  taskId: string
): Promise<ClusterStatusResponse> {
  const response = await apiClient.get<ClusterStatusResponse>(`/cluster/${taskId}`);
  return response.data;
}

export interface ClusterMatchedLinesResponse {
  cluster_index: number;
  group_key: string;
  matched_lines: CachedLogEntry[];
  total: number;
}

export async function getClusterMatchedLines(
  taskId: string,
  clusterIndex: number
): Promise<ClusterMatchedLinesResponse> {
  const response = await apiClient.get<ClusterMatchedLinesResponse>(
    `/cluster/${taskId}/matched-lines/${clusterIndex}`
  );
  return response.data;
}