import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private baseUrl = 'http://localhost:8000/api';

  constructor(private http: HttpClient) { }

  login(credentials: any): Observable<any> {
    return this.http.post(`${this.baseUrl}/users/login/`, credentials);
  }

  getDevices(token: string): Observable<any> {
    const headers = { 'Authorization': `Token ${token}` };
    return this.http.get(`${this.baseUrl}/devices/`, { headers });
  }

  createSession(token: string, data: any): Observable<any> {
    const headers = { 'Authorization': `Token ${token}` };
    return this.http.post(`${this.baseUrl}/sessions/`, data, { headers });
  }

  getMeasures(token: string, sessionId: string): Observable<any> {
    const headers = { 'Authorization': `Token ${token}` };
    return this.http.get(`${this.baseUrl}/sessions/${sessionId}/measures/`, { headers });
  }
}
