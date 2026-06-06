import { create } from 'zustand';
import api from '../services/api';
import type { JobLog } from '../types/job';

interface JobState {
  jobs: JobLog[];
  fetchJobs: () => Promise<void>;
}

export const useJobStore = create<JobState>((set) => ({
  jobs: [],
  fetchJobs: async () => {
    const { data } = await api.get('/jobs', { params: { limit: 50 } });
    set({ jobs: data.items });
  },
}));
