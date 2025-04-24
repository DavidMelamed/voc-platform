import React, { useState, useEffect } from 'react';
import { 
  Grid, 
  Card, 
  CardContent, 
  Typography, 
  Box, 
  Chip,
  Paper, 
  LinearProgress,
  CardHeader,
  Button,
  IconButton,
  Tooltip
} from '@mui/material';
import { 
  Refresh as RefreshIcon,
  Info as InfoIcon 
} from '@mui/icons-material';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';
import { format } from 'date-fns';
import { ResponsiveLine } from '@nivo/line';
import { ResponsivePie } from '@nivo/pie';

interface DashboardStats {
  documents_total: number;
  documents_today: number;
  sources_active: number;
  insights_total: number;
  insights_today: number;
  positive_sentiment: number;
  negative_sentiment: number;
  neutral_sentiment: number;
  urgent_count: number;
}

interface SentimentData {
  id: string;
  value: number;
  color: string;
}

interface TimelineData {
  id: string;
  data: Array<{ x: string; y: number }>;
}

interface TopTopic {
  topic: string;
  count: number;
  sentiment: 'positive' | 'negative' | 'neutral';
}

interface ActiveTask {
  id: string;
  task_type: string;
  source: string;
  status: string;
  progress: number;
  eta: string;
}

const Dashboard: React.FC = () => {
  const { tenantId } = useAuth();
  const [loading, setLoading] = useState<boolean>(true);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [sentimentData, setSentimentData] = useState<SentimentData[]>([]);
  const [timelineData, setTimelineData] = useState<TimelineData[]>([]);
  const [topTopics, setTopTopics] = useState<TopTopic[]>([]);
  const [activeTasks, setActiveTasks] = useState<ActiveTask[]>([]);
  const [refreshing, setRefreshing] = useState<boolean>(false);

  const fetchDashboardData = async () => {
    setRefreshing(true);
    try {
      // In a real implementation, these would be actual API calls
      // Fetch stats
      const statsResponse = await axios.get(`/api/dashboard/stats?tenant_id=${tenantId}`);
      setStats(statsResponse.data);

      // Fetch sentiment distribution
      const sentimentResponse = await axios.get(`/api/dashboard/sentiment?tenant_id=${tenantId}`);
      setSentimentData(sentimentResponse.data);

      // Fetch timeline data
      const timelineResponse = await axios.get(`/api/dashboard/timeline?tenant_id=${tenantId}&days=30`);
      setTimelineData(timelineResponse.data);

      // Fetch top topics
      const topicsResponse = await axios.get(`/api/dashboard/topics?tenant_id=${tenantId}&limit=5`);
      setTopTopics(topicsResponse.data);

      // Fetch active tasks
      const tasksResponse = await axios.get(`/api/tasks/active?tenant_id=${tenantId}`);
      setActiveTasks(tasksResponse.data);

    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      
      // For demo purposes, populate with mock data if the API fails
      setMockData();
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const setMockData = () => {
    // Stats
    setStats({
      documents_total: 4532,
      documents_today: 124,
      sources_active: 12,
      insights_total: 87,
      insights_today: 7,
      positive_sentiment: 45,
      negative_sentiment: 15,
      neutral_sentiment: 40,
      urgent_count: 8
    });

    // Sentiment data
    setSentimentData([
      { id: 'Positive', value: 45, color: '#4caf50' },
      { id: 'Negative', value: 15, color: '#f44336' },
      { id: 'Neutral', value: 40, color: '#9e9e9e' }
    ]);

    // Timeline data - 30 days
    const timelinePoints = [];
    const today = new Date();
    for (let i = 29; i >= 0; i--) {
      const date = new Date();
      date.setDate(today.getDate() - i);
      
      // Generate some random values
      timelinePoints.push({
        x: format(date, 'MMM dd'),
        y: Math.floor(Math.random() * 40) + 10 // Random between 10-50
      });
    }

    setTimelineData([
      {
        id: 'Documents',
        data: timelinePoints
      }
    ]);

    // Top topics
    setTopTopics([
      { topic: 'Customer Service', count: 245, sentiment: 'negative' },
      { topic: 'Product Quality', count: 187, sentiment: 'positive' },
      { topic: 'Shipping', count: 156, sentiment: 'negative' },
      { topic: 'Price', count: 132, sentiment: 'neutral' },
      { topic: 'App Experience', count: 98, sentiment: 'positive' }
    ]);

    // Active tasks
    setActiveTasks([
      { 
        id: 'task-1', 
        task_type: 'Website Scrape', 
        source: 'company-website.com', 
        status: 'In Progress', 
        progress: 45, 
        eta: '4 minutes' 
      },
      { 
        id: 'task-2', 
        task_type: 'Review Analysis', 
        source: 'trustpilot.com', 
        status: 'In Progress', 
        progress: 78, 
        eta: '1 minute' 
      },
      { 
        id: 'task-3', 
        task_type: 'Social Media Scan', 
        source: 'twitter.com', 
        status: 'Starting', 
        progress: 5, 
        eta: '12 minutes' 
      }
    ]);
  };

  useEffect(() => {
    fetchDashboardData();
  }, [tenantId]);

  const handleRefresh = () => {
    fetchDashboardData();
  };

  if (loading && !stats) {
    return <LinearProgress />;
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">Dashboard</Typography>
        <Button 
          variant="outlined" 
          startIcon={<RefreshIcon />}
          onClick={handleRefresh}
          disabled={refreshing}
        >
          Refresh
        </Button>
      </Box>

      {/* Stats Row */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>Total Documents</Typography>
              <Typography variant="h4">{stats?.documents_total.toLocaleString()}</Typography>
              <Typography variant="body2" color="textSecondary">
                +{stats?.documents_today} today
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>Active Sources</Typography>
              <Typography variant="h4">{stats?.sources_active}</Typography>
              <Typography variant="body2" color="textSecondary">
                Monitoring in real-time
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>Insights Generated</Typography>
              <Typography variant="h4">{stats?.insights_total}</Typography>
              <Typography variant="body2" color="textSecondary">
                +{stats?.insights_today} new insights today
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ bgcolor: stats && stats.urgent_count > 0 ? '#fffde7' : 'inherit' }}>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>Urgent Items</Typography>
              <Typography variant="h4" color={stats && stats.urgent_count > 0 ? 'error' : 'inherit'}>
                {stats?.urgent_count}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Require immediate attention
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Charts Row */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={8}>
          <Card>
            <CardHeader 
              title="Document Volume (30 Days)" 
              action={
                <Tooltip title="Documents collected over the past 30 days">
                  <IconButton>
                    <InfoIcon />
                  </IconButton>
                </Tooltip>
              }
            />
            <CardContent sx={{ height: 300 }}>
              {timelineData.length > 0 && (
                <ResponsiveLine
                  data={timelineData}
                  margin={{ top: 20, right: 20, bottom: 50, left: 60 }}
                  xScale={{ type: 'point' }}
                  yScale={{ type: 'linear', min: 'auto', max: 'auto' }}
                  curve="monotoneX"
                  axisBottom={{
                    tickRotation: -45,
                    tickSize: 5,
                  }}
                  axisLeft={{
                    tickSize: 5,
                    tickPadding: 5,
                    tickRotation: 0,
                  }}
                  colors={{ scheme: 'category10' }}
                  pointSize={10}
                  pointBorderWidth={2}
                  pointBorderColor={{ from: 'serieColor' }}
                  pointLabelYOffset={-12}
                  useMesh={true}
                />
              )}
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={4}>
          <Card>
            <CardHeader 
              title="Sentiment Distribution" 
              action={
                <Tooltip title="Distribution of sentiment in collected documents">
                  <IconButton>
                    <InfoIcon />
                  </IconButton>
                </Tooltip>
              }
            />
            <CardContent sx={{ height: 300 }}>
              {sentimentData.length > 0 && (
                <ResponsivePie
                  data={sentimentData}
                  margin={{ top: 20, right: 20, bottom: 20, left: 20 }}
                  innerRadius={0.5}
                  padAngle={0.7}
                  cornerRadius={3}
                  colors={{ datum: 'data.color' }}
                  borderWidth={1}
                  borderColor={{ from: 'color', modifiers: [['darker', 0.2]] }}
                  radialLabelsSkipAngle={10}
                  radialLabelsTextXOffset={6}
                  radialLabelsTextColor="#333333"
                  radialLabelsLinkOffset={0}
                  radialLabelsLinkDiagonalLength={16}
                  radialLabelsLinkHorizontalLength={24}
                  radialLabelsLinkStrokeWidth={1}
                  radialLabelsLinkColor={{ from: 'color' }}
                  slicesLabelsSkipAngle={10}
                  slicesLabelsTextColor="#333333"
                  animate={true}
                  motionStiffness={90}
                  motionDamping={15}
                />
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Topics and Tasks Rows */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardHeader title="Top Topics" />
            <CardContent>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                {topTopics.map((topic, index) => (
                  <Paper 
                    key={index} 
                    sx={{ 
                      p: 2, 
                      display: 'flex', 
                      justifyContent: 'space-between', 
                      alignItems: 'center',
                      borderLeft: '4px solid',
                      borderColor: 
                        topic.sentiment === 'positive' ? '#4caf50' : 
                        topic.sentiment === 'negative' ? '#f44336' : '#9e9e9e'
                    }}
                  >
                    <Typography variant="body1">{topic.topic}</Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                      <Typography variant="body2" color="textSecondary">
                        {topic.count} mentions
                      </Typography>
                      <Chip 
                        label={topic.sentiment} 
                        size="small"
                        sx={{
                          bgcolor: 
                            topic.sentiment === 'positive' ? '#e8f5e9' : 
                            topic.sentiment === 'negative' ? '#ffebee' : '#f5f5f5',
                          color: 
                            topic.sentiment === 'positive' ? '#2e7d32' : 
                            topic.sentiment === 'negative' ? '#c62828' : '#757575',
                        }}
                      />
                    </Box>
                  </Paper>
                ))}
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Card>
            <CardHeader title="Active Tasks" />
            <CardContent>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                {activeTasks.length > 0 ? (
                  activeTasks.map((task, index) => (
                    <Paper key={index} sx={{ p: 2 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                        <Typography variant="body1">{task.task_type}</Typography>
                        <Chip 
                          label={task.status} 
                          size="small"
                          color={
                            task.status === 'In Progress' ? 'primary' : 
                            task.status === 'Starting' ? 'secondary' : 'default'
                          }
                          variant="outlined"
                        />
                      </Box>
                      <Typography variant="body2" color="textSecondary" sx={{ mb: 1 }}>
                        Source: {task.source}
                      </Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                        <LinearProgress 
                          variant="determinate" 
                          value={task.progress} 
                          sx={{ flexGrow: 1 }}
                        />
                        <Typography variant="body2" color="textSecondary">
                          {task.progress}% • ETA: {task.eta}
                        </Typography>
                      </Box>
                    </Paper>
                  ))
                ) : (
                  <Typography variant="body1" color="textSecondary" align="center">
                    No active tasks at the moment
                  </Typography>
                )}
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;
