import { Component, OnInit, OnDestroy, AfterViewInit, ViewChild, ElementRef } from '@angular/core';
import { ApiService } from '../services/api.service';
import { Chart, registerables } from 'chart.js';

Chart.register(...registerables);

// --- Configuration de la détection de mensonges ---
const ROLLING_WINDOW = 5;       // Nombre de mesures pour la moyenne glissante (demandé : les 5 dernières)
const LIE_DELTA_RATIO = 0.18;  // +18% au-dessus de la moyenne glissante = mensonge
const MAX_CHART_POINTS = 60;    // Augmenté pour garder 30s de données à 500ms

// --- Configuration Tremblements ---
const TREMOR_WINDOW = 5;
const TREMOR_RATIO = 0.30;       // +30% au-dessus de la moyenne = alerte

@Component({
  selector: 'app-dashboard',
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.css']
})
export class DashboardComponent implements OnInit, OnDestroy, AfterViewInit {
  @ViewChild('bpmChart') bpmChartRef!: ElementRef;

  token: string | null = null;
  username = '';
  password = '';

  devices: any[] = [];
  selectedDeviceId: string = '';

  currentSessionId: string | null = null;
  measures: any[] = [];

  // Lie detection state
  isLieAlert: boolean = false;
  rollingAvg: number = 0;
  currentBpm: number = 0;
  delta: number = 0;           // BPM - rollingAvg
  deltaPercent: number = 0;    // % d'écart par rapport à la moyenne
  currentShake: number = 0;    // Tremblement actuel (M5StickC)

  pollingInterval: any;
  chart: Chart | null = null;
  tremorChart: Chart | null = null;
  isTremorAlert: boolean = false;
  tremorRollingAvg: number = 0;

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    const storedToken = localStorage.getItem('token');
    if (storedToken) {
      this.token = storedToken;
      this.loadDevices();
    }
  }

  ngAfterViewInit(): void {}

  ngOnDestroy(): void {
    this.stopPolling();
    if (this.chart) this.chart.destroy();
  }

  login() {
    this.api.login({ username: this.username, password: this.password }).subscribe({
      next: (res) => {
        this.token = res.token;
        if (this.token) {
          localStorage.setItem('token', this.token);
          this.loadDevices();
        }
      },
      error: () => alert('Login failed: identifiants incorrects.')
    });
  }

  logout() {
    this.token = null;
    localStorage.removeItem('token');
    this.stopPolling();
    if (this.chart) { this.chart.destroy(); this.chart = null; }
    this.measures = [];
    this.currentSessionId = null;
  }

  loadDevices() {
    if (!this.token) return;
    this.api.getDevices(this.token).subscribe({
      next: (res) => {
        this.devices = res;
        if (res.length > 0) this.selectedDeviceId = res[0].id;
      },
      error: (err) => console.error(err)
    });
  }

  startSession() {
    if (!this.token || !this.selectedDeviceId) return;
    this.measures = [];
    this.isLieAlert = false;
    this.stopPolling();
    if (this.chart) { this.chart.destroy(); this.chart = null; }

    this.api.createSession(this.token, {
      device_id: this.selectedDeviceId,
      calibration_base_bpm: 70
    }).subscribe({
      next: (res) => {
        this.currentSessionId = res.id;
        this.initChart();
        this.startPolling();
      },
      error: (err) => alert('Failed to start session: ' + JSON.stringify(err))
    });
  }

  initChart() {
    setTimeout(() => {
      const canvas = document.getElementById('bpmChart') as HTMLCanvasElement;
      if (!canvas) return;
      if (this.chart) this.chart.destroy();

      this.chart = new Chart(canvas, {
        type: 'line',
        data: {
          labels: [],
          datasets: [
            {
              label: 'BPM',
              data: [],
              borderColor: '#6366f1',
              backgroundColor: 'rgba(99, 102, 241, 0.08)',
              borderWidth: 2.5,
              tension: 0.4,
              pointRadius: 4,
              pointHoverRadius: 6,
              fill: true,
              pointBackgroundColor: [],
            },
            {
              label: `Moyenne glissante (${ROLLING_WINDOW} pts)`,
              data: [],
              borderColor: '#f59e0b',
              borderWidth: 2,
              borderDash: [6, 4],
              tension: 0.4,
              pointRadius: 0,
              fill: false,
            },
            {
              label: `Seuil mensonge (+${Math.round(LIE_DELTA_RATIO * 100)}%)`,
              data: [],
              borderColor: '#ef4444',
              borderWidth: 1.5,
              borderDash: [3, 6],
              tension: 0.4,
              pointRadius: 0,
              fill: false,
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          animation: { duration: 300 },
          scales: {
            x: {
              ticks: { color: '#94a3b8', font: { size: 11 }, maxTicksLimit: 10 },
              grid: { color: 'rgba(148,163,184,0.1)' }
            },
            y: {
              ticks: { color: '#94a3b8', font: { size: 11 } },
              grid: { color: 'rgba(148,163,184,0.1)' },
              title: { display: true, text: 'BPM', color: '#94a3b8' }
            }
          },
          plugins: {
            legend: {
              labels: { color: '#cbd5e1', font: { size: 12 } }
            },
            tooltip: {
              callbacks: {
                label: (ctx: any) => ` ${ctx.dataset.label}: ${Number(ctx.parsed.y).toFixed(1)} BPM`
              }
            }
          }
        }
      });

      // --- Tremor Chart Initialization ---
      const tremorCanvas = document.getElementById('tremorChart') as HTMLCanvasElement;
      if (!tremorCanvas) return;
      if (this.tremorChart) this.tremorChart.destroy();

      this.tremorChart = new Chart(tremorCanvas, {
        type: 'line',
        data: {
          labels: [],
          datasets: [
            {
              label: 'Vibrations',
              data: [],
              borderColor: '#818cf8',
              backgroundColor: 'rgba(129, 140, 248, 0.08)',
              borderWidth: 2,
              tension: 0.4,
              pointRadius: 3,
              fill: true,
              pointBackgroundColor: [],
            },
            {
              label: 'Seuil Alerte',
              data: [],
              borderColor: '#f87171',
              borderWidth: 1.5,
              borderDash: [4, 4],
              tension: 0.4,
              pointRadius: 0,
              fill: false,
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            x: { ticks: { display: false }, grid: { display: false } },
            y: {
              beginAtZero: true,
              ticks: { color: '#94a3b8', font: { size: 10 } },
              grid: { color: 'rgba(148,163,184,0.1)' }
            }
          },
          plugins: { legend: { display: false } }
        }
      });
    }, 100);
  }

  startPolling() {
    this.pollingInterval = setInterval(() => this.fetchMeasures(), 500);
  }

  stopPolling() {
    if (this.pollingInterval) clearInterval(this.pollingInterval);
  }

  fetchMeasures() {
    if (!this.token || !this.currentSessionId) return;
    this.api.getMeasures(this.token, this.currentSessionId).subscribe({
      next: (res: any[]) => {
        if (!res || res.length === 0) return;

        // Sort oldest → newest
        const sorted = [...res].sort((a, b) =>
          new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
        );

        this.measures = sorted;
        this.updateLieDetection(sorted);
        this.updateChart(sorted);
      },
      error: (err) => console.error(err)
    });
  }

  // --- Logique de détection de mensonge côté frontend ---
  updateLieDetection(sorted: any[]) {
    if (sorted.length === 0) return;

    const latest = sorted[sorted.length - 1];
    this.currentBpm = latest.bpm;
    this.currentShake = latest.shake_intensity || 0;

    // Fenêtre glissante : exclut le point courant pour ne pas biaiser
    const windowData = sorted.slice(
      Math.max(0, sorted.length - 1 - ROLLING_WINDOW),
      sorted.length - 1
    );

    if (windowData.length === 0) {
      this.rollingAvg = this.currentBpm;
    } else {
      this.rollingAvg = windowData.reduce((s: number, m: any) => s + m.bpm, 0) / windowData.length;
    }

    this.delta = this.currentBpm - this.rollingAvg;
    this.deltaPercent = this.rollingAvg > 0 ? (this.delta / this.rollingAvg) * 100 : 0;
    this.isLieAlert = this.deltaPercent > LIE_DELTA_RATIO * 100;

    // Tremor Alert Logic
    const tremorWindow = sorted.slice(
      Math.max(0, sorted.length - 1 - TREMOR_WINDOW),
      sorted.length - 1
    );
    if (tremorWindow.length === 0) {
      this.tremorRollingAvg = this.currentShake;
    } else {
      this.tremorRollingAvg = tremorWindow.reduce((s: number, m: any) => s + (m.shake_intensity || 0), 0) / tremorWindow.length;
    }
    this.isTremorAlert = this.currentShake > (this.tremorRollingAvg * (1 + TREMOR_RATIO)) && this.currentShake > 0.2;
  }

  updateChart(sorted: any[]) {
    if (!this.chart) return;

    // Limit displayed points
    const visible = sorted.slice(-MAX_CHART_POINTS);

    const labels = visible.map((m: any) => {
      const d = new Date(m.timestamp);
      return `${d.getHours().toString().padStart(2,'0')}:${d.getMinutes().toString().padStart(2,'0')}:${d.getSeconds().toString().padStart(2,'0')}`;
    });

    const bpmData = visible.map((m: any) => m.bpm);

    // Compute rolling average for each visible point
    const avgData = visible.map((_: any, i: number) => {
      const allUpToI = sorted.slice(0, sorted.length - visible.length + i + 1);
      const win = allUpToI.slice(Math.max(0, allUpToI.length - 1 - ROLLING_WINDOW), allUpToI.length - 1);
      if (win.length === 0) return bpmData[0];
      return win.reduce((s: number, m: any) => s + m.bpm, 0) / win.length;
    });

    const thresholdData = avgData.map((avg: number) => avg * (1 + LIE_DELTA_RATIO));

    // Color each BPM point: red if above threshold, indigo otherwise
    const pointColors = bpmData.map((bpm: number, i: number) =>
      bpm > thresholdData[i] ? '#ef4444' : '#6366f1'
    );

    this.chart.data.labels = labels;
    this.chart.data.datasets[0].data = bpmData;
    (this.chart.data.datasets[0] as any).pointBackgroundColor = pointColors;
    this.chart.data.datasets[1].data = avgData;
    this.chart.data.datasets[2].data = thresholdData;
    this.chart.update('none');

    // Update Tremor Chart
    if (!this.tremorChart) return;
    const shakeData = visible.map((m: any) => m.shake_intensity || 0);
    const tremorThresholdData = visible.map((_: any, i: number) => {
        const allUpToI = sorted.slice(0, sorted.length - visible.length + i + 1);
        const win = allUpToI.slice(Math.max(0, allUpToI.length - 1 - TREMOR_WINDOW), allUpToI.length - 1);
        const avg = win.length === 0 ? shakeData[0] : win.reduce((s: number, m: any) => s + (m.shake_intensity || 0), 0) / win.length;
        return avg * (1 + TREMOR_RATIO);
    });

    this.tremorChart.data.labels = labels;
    this.tremorChart.data.datasets[0].data = shakeData;
    this.tremorChart.data.datasets[1].data = tremorThresholdData;
    (this.tremorChart.data.datasets[0] as any).pointBackgroundColor = shakeData.map((s: number, i: number) => s > tremorThresholdData[i] ? '#ef4444' : '#818cf8');
    this.tremorChart.update('none');
  }

  get lieThreshold(): number {
    return this.rollingAvg * (1 + LIE_DELTA_RATIO);
  }

  // For the history table: measures are shown reversed (latest first), 
  // so i=0 is the most recent. Convert back to chronological index.
  computeRollingAvg(reversedIndex: number): number {
    const chronoIndex = this.measures.length - 1 - reversedIndex;
    const win = this.measures.slice(
      Math.max(0, chronoIndex - ROLLING_WINDOW),
      chronoIndex
    );
    if (win.length === 0) return this.measures[chronoIndex]?.bpm ?? 0;
    return win.reduce((s: number, m: any) => s + m.bpm, 0) / win.length;
  }

  computeDeltaPercent(reversedIndex: number): number {
    const chronoIndex = this.measures.length - 1 - reversedIndex;
    const avg = this.computeRollingAvg(reversedIndex);
    const bpm = this.measures[chronoIndex]?.bpm ?? 0;
    return avg > 0 ? ((bpm - avg) / avg) * 100 : 0;
  }
}
