import { MetricCard } from '@/components/MetricCard';
import { ReplyItem } from '@/components/ReplyItem';
import { StatusBadge } from '@/components/StatusBadge';
import { PlatformTag } from '@/components/PlatformTag';
import { mockContents, mockMonitorData, mockEngagementTrend } from '@/data/mock';
import { Heart, MessageCircle, Share2, TrendingUp, FileText, CheckCircle, AlertTriangle } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';

export default function MonitorDashboard() {
  const publishedContents = mockContents.filter(c => ['success', 'partial_success'].includes(c.status));
  const totalLikes = mockMonitorData.reduce((sum, d) => sum + d.likes, 0);
  const totalComments = mockMonitorData.reduce((sum, d) => sum + d.comments, 0);
  const totalShares = mockMonitorData.reduce((sum, d) => sum + d.shares, 0);
  const allReplies = mockMonitorData
    .flatMap(d => d.recent_replies)
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());

  const statusCounts = {
    total: mockContents.length,
    success: mockContents.filter(c => c.status === 'success').length,
    failed: mockContents.filter(c => c.status === 'failed').length + mockContents.filter(c => c.status === 'partial_success').length,
  };

  return (
    <div className="p-6 lg:p-8 max-w-7xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-display font-semibold text-foreground">監控儀表板</h1>
        <p className="text-sm text-muted-foreground mt-1">追蹤你的內容表現與互動數據</p>
      </div>

      {/* Bento Metrics Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard title="總互動數" value={totalLikes + totalComments + totalShares} icon={TrendingUp} trend={{ value: 12.5, label: '較上週' }} />
        <MetricCard title="按讚數" value={totalLikes} icon={Heart} trend={{ value: 8.3, label: '較上週' }} />
        <MetricCard title="留言數" value={totalComments} icon={MessageCircle} trend={{ value: 15.2, label: '較上週' }} />
        <MetricCard title="分享數" value={totalShares} icon={Share2} trend={{ value: 5.1, label: '較上週' }} />
      </div>

      {/* Second Row: Chart + Status Overview */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Engagement Trend Chart */}
        <div className="lg:col-span-2 bg-card rounded-xl border border-border/40 p-5">
          <h2 className="font-display text-lg font-semibold text-card-foreground mb-4">互動趨勢</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={mockEngagementTrend}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis dataKey="date" stroke="hsl(var(--muted-foreground))" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} tickLine={false} axisLine={false} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'hsl(var(--card))',
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '8px',
                    fontSize: '12px',
                  }}
                />
                <Line type="monotone" dataKey="likes" stroke="hsl(var(--primary))" strokeWidth={2} dot={false} name="按讚" />
                <Line type="monotone" dataKey="comments" stroke="hsl(var(--success))" strokeWidth={2} dot={false} name="留言" />
                <Line type="monotone" dataKey="shares" stroke="hsl(var(--info))" strokeWidth={2} dot={false} name="分享" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Status Overview */}
        <div className="bg-card rounded-xl border border-border/40 p-5 space-y-4">
          <h2 className="font-display text-lg font-semibold text-card-foreground">發佈總覽</h2>
          <div className="space-y-3">
            <div className="flex items-center justify-between py-2">
              <div className="flex items-center gap-2">
                <FileText className="w-4 h-4 text-muted-foreground" strokeWidth={1.5} />
                <span className="text-sm text-muted-foreground">總貼文數</span>
              </div>
              <span className="font-display text-xl font-semibold">{statusCounts.total}</span>
            </div>
            <div className="flex items-center justify-between py-2">
              <div className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-success" strokeWidth={1.5} />
                <span className="text-sm text-muted-foreground">發佈成功</span>
              </div>
              <span className="font-display text-xl font-semibold text-success">{statusCounts.success}</span>
            </div>
            <div className="flex items-center justify-between py-2">
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-warning" strokeWidth={1.5} />
                <span className="text-sm text-muted-foreground">需處理</span>
              </div>
              <span className="font-display text-xl font-semibold text-warning">{statusCounts.failed}</span>
            </div>
          </div>

          {/* Success Rate */}
          <div className="pt-3 border-t border-border/30">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs text-muted-foreground">發佈成功率</span>
              <span className="text-xs font-medium">{Math.round((statusCounts.success / statusCounts.total) * 100)}%</span>
            </div>
            <div className="w-full h-2 bg-muted rounded-full overflow-hidden">
              <div
                className="h-full bg-success rounded-full transition-all"
                style={{ width: `${(statusCounts.success / statusCounts.total) * 100}%` }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Third Row: Per-Content Engagement + Recent Replies */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Per-Content Engagement */}
        <div className="bg-card rounded-xl border border-border/40 p-5">
          <h2 className="font-display text-lg font-semibold text-card-foreground mb-4">各貼文表現</h2>
          <div className="space-y-4">
            {publishedContents.map(content => {
              const contentMonitor = mockMonitorData.filter(d => d.content_id === content.id);
              const likes = contentMonitor.reduce((s, d) => s + d.likes, 0);
              const comments = contentMonitor.reduce((s, d) => s + d.comments, 0);
              const shares = contentMonitor.reduce((s, d) => s + d.shares, 0);
              return (
                <div key={content.id} className="flex items-start gap-3 p-3 rounded-lg hover:bg-muted/50 transition-colors">
                  {content.image_url && (
                    <img src={content.image_url} alt="" className="w-12 h-12 rounded-lg object-cover shrink-0" />
                  )}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <h4 className="text-sm font-medium text-foreground truncate">{content.title}</h4>
                      <StatusBadge status={content.status} />
                    </div>
                    <div className="flex items-center gap-1 mb-2">
                      {content.platforms.map(p => <PlatformTag key={p} platform={p} />)}
                    </div>
                    <div className="flex items-center gap-4 text-xs text-muted-foreground">
                      <span className="flex items-center gap-1"><Heart className="w-3 h-3" /> {likes.toLocaleString()}</span>
                      <span className="flex items-center gap-1"><MessageCircle className="w-3 h-3" /> {comments}</span>
                      <span className="flex items-center gap-1"><Share2 className="w-3 h-3" /> {shares}</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Recent Replies */}
        <div className="bg-card rounded-xl border border-border/40 p-5">
          <h2 className="font-display text-lg font-semibold text-card-foreground mb-4">最新回覆</h2>
          <div className="space-y-0">
            {allReplies.slice(0, 8).map((reply, i) => (
              <ReplyItem key={i} reply={reply} />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
