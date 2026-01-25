import { useState, useEffect } from 'react';
import { reportsApi } from '../api/client';
import type { Report } from '../types';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Download } from 'lucide-react';

export default function Reports() {
  const [report, setReport] = useState<Report | null>(null);
  const [period, setPeriod] = useState<'week' | 'month'>('week');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadReport();
  }, [period]);

  const loadReport = async () => {
    setLoading(true);
    try {
      const res = period === 'week'
        ? await reportsApi.getWeek()
        : await reportsApi.getMonth();
      setReport(res.data);
    } catch (error) {
      console.error('Error loading report:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleExportCSV = async () => {
    try {
      const res = await reportsApi.exportWeekCSV();
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'rivaflow_report.csv');
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error('Error exporting CSV:', error);
    }
  };

  if (loading) {
    return <div className="text-center py-12">Loading...</div>;
  }

  if (!report) {
    return <div className="text-center py-12">No data available</div>;
  }

  // Prepare chart data
  const chartData = Object.entries(report.breakdown_by_type).map(([type, data]) => ({
    name: type,
    classes: data.classes,
    hours: data.hours,
    rolls: data.rolls,
  }));

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Training Reports</h1>
        <button onClick={handleExportCSV} className="btn-secondary flex items-center gap-2">
          <Download className="w-4 h-4" />
          Export CSV
        </button>
      </div>

      {/* Period Selector */}
      <div className="flex gap-2">
        <button
          onClick={() => setPeriod('week')}
          className={period === 'week' ? 'btn-primary' : 'btn-secondary'}
        >
          Week
        </button>
        <button
          onClick={() => setPeriod('month')}
          className={period === 'month' ? 'btn-primary' : 'btn-secondary'}
        >
          Month
        </button>
      </div>

      <div className="card">
        <h2 className="text-xl font-semibold mb-4">
          {new Date(report.start_date).toLocaleDateString()} - {new Date(report.end_date).toLocaleDateString()}
        </h2>

        {report.summary.total_classes === 0 ? (
          <p className="text-center text-gray-500 dark:text-gray-400 py-8">
            No sessions logged for this period
          </p>
        ) : (
          <>
            {/* Summary Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Total Classes</p>
                <p className="text-2xl font-bold">{report.summary.total_classes}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Total Hours</p>
                <p className="text-2xl font-bold">{report.summary.total_hours}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Total Rolls</p>
                <p className="text-2xl font-bold">{report.summary.total_rolls}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Avg Intensity</p>
                <p className="text-2xl font-bold">{report.summary.avg_intensity}/5</p>
              </div>
            </div>

            {/* Submission Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <div>
                <p className="text-xs text-gray-600 dark:text-gray-400">Subs For</p>
                <p className="text-xl font-bold">{report.summary.submissions_for}</p>
              </div>
              <div>
                <p className="text-xs text-gray-600 dark:text-gray-400">Subs Against</p>
                <p className="text-xl font-bold">{report.summary.submissions_against}</p>
              </div>
              <div>
                <p className="text-xs text-gray-600 dark:text-gray-400">Subs/Roll</p>
                <p className="text-xl font-bold">{report.summary.subs_per_roll.toFixed(2)}</p>
              </div>
              <div>
                <p className="text-xs text-gray-600 dark:text-gray-400">Sub Ratio</p>
                <p className="text-xl font-bold">{report.summary.sub_ratio.toFixed(2)}</p>
              </div>
            </div>

            {/* Chart */}
            <div className="mb-6">
              <h3 className="text-lg font-semibold mb-3">Breakdown by Type</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="classes" fill="#0ea5e9" name="Classes" />
                  <Bar dataKey="rolls" fill="#10b981" name="Rolls" />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Gym Breakdown */}
            <div>
              <h3 className="text-lg font-semibold mb-3">Breakdown by Gym</h3>
              <div className="space-y-2">
                {Object.entries(report.breakdown_by_gym).map(([gym, count]) => (
                  <div key={gym} className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-700 rounded">
                    <span>{gym}</span>
                    <span className="font-semibold">{count} classes</span>
                  </div>
                ))}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
