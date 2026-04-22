import { Separator } from "@/components/ui/separator";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useState } from "react";

export default function SettingsPage() {
  const [n8nUrl, setN8nUrl] = useState('http://localhost:5678');

  return (
    <div className="p-6 lg:p-8 max-w-3xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl font-display font-semibold text-foreground">設定</h1>
        <p className="text-sm text-muted-foreground mt-1">管理平台連線與通知偏好</p>
      </div>

      {/* n8n Connection */}
      <section className="bg-card rounded-xl border border-border/40 p-6 space-y-4">
        <h2 className="font-display text-lg font-semibold text-card-foreground">n8n 連線設定</h2>
        <div className="space-y-3">
          <div className="space-y-1.5">
            <Label htmlFor="n8n-url" className="text-sm">Webhook URL</Label>
            <Input
              id="n8n-url"
              value={n8nUrl}
              onChange={e => setN8nUrl(e.target.value)}
              placeholder="https://your-n8n-instance.com"
              className="bg-background"
            />
          </div>
          <Button size="sm" variant="outline">測試連線</Button>
        </div>
      </section>

      <Separator />

      {/* Platform Connections */}
      <section className="bg-card rounded-xl border border-border/40 p-6 space-y-4">
        <h2 className="font-display text-lg font-semibold text-card-foreground">平台連線狀態</h2>
        <div className="space-y-3">
          {[
            { name: 'Facebook Page', connected: true },
            { name: 'Instagram Professional', connected: false },
            { name: 'X (Twitter)', connected: true },
            { name: 'LINE Official Account', connected: true },
          ].map(p => (
            <div key={p.name} className="flex items-center justify-between py-2">
              <span className="text-sm text-foreground">{p.name}</span>
              <span className={`text-xs font-medium px-2.5 py-0.5 rounded-full ${
                p.connected
                  ? 'bg-success/15 text-success'
                  : 'bg-muted text-muted-foreground'
              }`}>
                {p.connected ? '已連線' : '未連線'}
              </span>
            </div>
          ))}
        </div>
      </section>

      <Separator />

      {/* Notifications */}
      <section className="bg-card rounded-xl border border-border/40 p-6 space-y-4">
        <h2 className="font-display text-lg font-semibold text-card-foreground">通知設定</h2>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-foreground">發佈失敗通知</p>
              <p className="text-xs text-muted-foreground">發佈失敗時透過 Email 通知</p>
            </div>
            <Switch defaultChecked />
          </div>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-foreground">互動異常告警</p>
              <p className="text-xs text-muted-foreground">貼文互動異常時發送通知</p>
            </div>
            <Switch />
          </div>
        </div>
      </section>
    </div>
  );
}
