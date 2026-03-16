import { Component, OnInit, OnDestroy } from '@angular/core';
import { ApiService } from '../services/api.service';

@Component({
  selector: 'app-dashboard',
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.css']
})
export class DashboardComponent implements OnInit, OnDestroy {
  token: string | null = null;
  username = '';
  password = '';
  
  devices: any[] = [];
  selectedDeviceId: string = '';
  
  currentSessionId: string | null = null;
  measures: any[] = [];
  isLieAlert: boolean = false;
  
  pollingInterval: any;

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    // Check if logged in
    const storedToken = localStorage.getItem('token');
    if (storedToken) {
      this.token = storedToken;
      this.loadDevices();
    }
  }

  ngOnDestroy(): void {
    if (this.pollingInterval) {
      clearInterval(this.pollingInterval);
    }
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
      error: (err) => alert('Login failed: ' + JSON.stringify(err))
    });
  }

  logout() {
    this.token = null;
    localStorage.removeItem('token');
    this.stopPolling();
  }

  loadDevices() {
    if (!this.token) return;
    this.api.getDevices(this.token).subscribe({
      next: (res) => {
        this.devices = res;
        if (res.length > 0) {
          this.selectedDeviceId = res[0].id; // Select first device by default
        }
      },
      error: (err) => console.error(err)
    });
  }

  startSession() {
    if (!this.token || !this.selectedDeviceId) return;
    
    // Default calibration assumption, can be updated by actual M5 later
    this.api.createSession(this.token, { 
      device_id: this.selectedDeviceId,
      calibration_base_bpm: 70 
    }).subscribe({
      next: (res) => {
        this.currentSessionId = res.id;
        this.measures = [];
        this.isLieAlert = false;
        this.startPolling();
      },
      error: (err) => alert('Failed to start session: ' + JSON.stringify(err))
    });
  }

  startPolling() {
    if (this.pollingInterval) clearInterval(this.pollingInterval);
    
    this.pollingInterval = setInterval(() => {
      this.fetchMeasures();
    }, 2000); // Poll every 2 seconds
  }

  stopPolling() {
    if (this.pollingInterval) clearInterval(this.pollingInterval);
  }

  fetchMeasures() {
    if (!this.token || !this.currentSessionId) return;
    
    this.api.getMeasures(this.token, this.currentSessionId).subscribe({
      next: (res) => {
        this.measures = res;
        
        // Check for lie in the latest measure
        if (this.measures.length > 0) {
          const latest = this.measures[this.measures.length - 1];
          this.isLieAlert = latest.is_lie;
        } else {
          this.isLieAlert = false;
        }
      },
      error: (err) => console.error(err)
    });
  }
}
