import { useJobStore } from '../../stores/jobStore';
import { usePoll } from '../../hooks/usePoll';
import { theme } from '../../styles/theme';
import { JobStatusList } from './JobStatusList';
import { MapReduceJobForm } from './MapReduceJobForm';
import { MLTrainForm } from './MLTrainForm';

const POLL_MS = Number(import.meta.env.VITE_POLL_JOBS_MS);

export function JobsPage() {
  const { jobs, fetchJobs } = useJobStore();
  usePoll(fetchJobs, POLL_MS);

  return (
    <div>
      <h1 style={{ color: theme.colors.primary }}>Processing Jobs</h1>
      <section style={{ marginBottom: theme.spacing.xl }}>
        <h2>MapReduce</h2>
        <MapReduceJobForm onSubmitted={fetchJobs} />
      </section>
      <section style={{ marginBottom: theme.spacing.xl }}>
        <h2>Machine Learning</h2>
        <MLTrainForm onSubmitted={fetchJobs} />
      </section>
      <section>
        <h2>Job History</h2>
        <JobStatusList jobs={jobs} />
      </section>
    </div>
  );
}
