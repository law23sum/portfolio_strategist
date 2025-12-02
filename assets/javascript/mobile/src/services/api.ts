import AsyncStorage from '@react-native-async-storage/async-storage';
import { Platform } from 'react-native';
import { API_BASE_URL, API_ENDPOINTS, setApiBaseUrl } from '../config/api';

const TOKEN_KEY = 'accessToken';
const REFRESH_TOKEN_KEY = 'refreshToken';

export interface ApiResponse<T> {
  data?: T;
  error?: string;
  status: number;
}

export interface StockDetailsResponse {
  success?: boolean;
  symbol: string;
  stock_data?: Record<string, any>;
  key_metrics?: Record<string, any>;
  historical_data?: Array<Record<string, any>>;
  ratios?: Array<Record<string, any>>;
  news_html?: string;
  yahoo_finance?: {
    summary?: Record<string, any>;
    news?: Array<Record<string, any>>;
    chart_details?: Record<string, any>;
    statistics?: Record<string, any>;
    options?: Record<string, any>;
    holders?: Record<string, any>;
    profile?: Record<string, any>;
  };
  sources_used?: string[];
}

class ApiService {
  private baseURL: string;
  private refreshTokenPromise: Promise<boolean> | null = null;
  private isRefreshing: boolean = false;

  constructor() {
    // Sanitize base URL - remove trailing slashes and any invalid characters
    this.baseURL = API_BASE_URL.replace(/\/+$/, '').trim();
    console.log(`[API] Initialized with base URL: ${this.baseURL}`);
    console.log(`[API] Platform: ${Platform.OS}`);
    if (__DEV__) {
      console.log(`[API] Development mode - using ${this.baseURL}`);
      console.log(`[API] To change URL: import { setApiBaseUrl } from '../config/api' and call setApiBaseUrl('http://YOUR_IP:8000')`);
    }
  }

  /**
   * Update the base URL at runtime (useful for switching between simulator and physical device)
   * @param url - The new base URL (e.g., 'http://192.168.1.100:8000')
   */
  updateBaseURL(url: string): void {
    if (typeof url === 'string' && url.trim().length > 0) {
      setApiBaseUrl(url);
      this.baseURL = url.replace(/\/+$/, '').trim();
      console.log(`[API] Base URL updated to: ${this.baseURL}`);
    } else {
      console.warn(`[API] Invalid URL provided: ${url}`);
    }
  }

  private async getToken(): Promise<string | null> {
    return await AsyncStorage.getItem(TOKEN_KEY);
  }

  private async getRefreshToken(): Promise<string | null> {
    return await AsyncStorage.getItem(REFRESH_TOKEN_KEY);
  }

  private async setTokens(accessToken: string, refreshToken: string): Promise<void> {
    await AsyncStorage.multiSet([
      [TOKEN_KEY, accessToken],
      [REFRESH_TOKEN_KEY, refreshToken],
    ]);
  }

  private async clearTokens(): Promise<void> {
    await AsyncStorage.multiRemove([TOKEN_KEY, REFRESH_TOKEN_KEY]);
  }

  private async refreshAccessToken(): Promise<boolean> {
    // If already refreshing, return the existing promise
    if (this.isRefreshing && this.refreshTokenPromise) {
      return this.refreshTokenPromise;
    }

    // Start a new refresh
    this.isRefreshing = true;
    this.refreshTokenPromise = this._doRefreshToken();

    try {
      const result = await this.refreshTokenPromise;
      return result;
    } finally {
      this.isRefreshing = false;
      this.refreshTokenPromise = null;
    }
  }

  private async _doRefreshToken(): Promise<boolean> {
    try {
      const refreshToken = await this.getRefreshToken();
      if (!refreshToken) {
        return false;
      }

      const response = await fetch(`${this.baseURL}${API_ENDPOINTS.AUTH.TOKEN_REFRESH}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refresh: refreshToken }),
      });

      if (response.ok) {
        const data = await response.json();
        if (data.access) {
          await AsyncStorage.setItem(TOKEN_KEY, data.access);
          return true;
        }
      }
      return false;
    } catch (error) {
      console.error('Token refresh error:', error);
      return false;
    }
  }

  private async makeRequest<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    try {
      const token = await this.getToken();
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        ...options.headers,
      };

      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      // Ensure endpoint starts with / and sanitize URL construction
      const sanitizedEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
      const url = `${this.baseURL}${sanitizedEndpoint}`;
      
      // Validate URL doesn't have invalid characters
      if (url.includes('~') || url.includes(' ')) {
        console.error(`[API] Invalid URL detected: ${url}`);
        return {
          status: 0,
          error: `Invalid URL format: ${url}`,
        };
      }
      
      console.log(`[API] Making request to: ${url}`);
      console.log(`[API] Method: ${options.method || 'GET'}`);
      console.log(`[API] Base URL: ${this.baseURL}`);
      console.log(`[API] Endpoint: ${sanitizedEndpoint}`);

      let response: Response;
      try {
        // Add timeout for iOS network requests (React Native fetch supports AbortController)
        let timeoutId: NodeJS.Timeout | null = null;
        let controller: AbortController | null = null;
        
        // Only use AbortController if available (React Native 0.60+)
        if (typeof AbortController !== 'undefined') {
          controller = new AbortController();
          timeoutId = setTimeout(() => {
            if (controller) {
              controller.abort();
            }
          }, 30000); // 30 second timeout
        }
        
        response = await fetch(url, {
          ...options,
          headers,
          ...(controller && { signal: controller.signal }),
        });
        
        if (timeoutId) {
          clearTimeout(timeoutId);
        }
      } catch (fetchError: any) {
        console.error('[API] Fetch error:', fetchError);
        console.error('[API] Error details:', {
          message: fetchError.message,
          name: fetchError.name,
          code: fetchError.code,
          url,
        });
        
        // Provide more specific error messages based on error type
        let errorMessage = 'Unable to connect to server.';
        if (fetchError.name === 'AbortError') {
          errorMessage = 'Request timed out. The server may be slow or unreachable.';
        } else if (fetchError.message) {
          if (fetchError.message.includes('Network request failed') || 
              fetchError.message.includes('network request failed') ||
              fetchError.message.includes('NetworkError') ||
              fetchError.message.toLowerCase().includes('network')) {
            const isLocalhost = this.baseURL.includes('localhost') || this.baseURL.includes('127.0.0.1');
            const deviceHint = isLocalhost 
              ? '\n⚠️ If you\'re on a physical iOS device, localhost won\'t work!\n   Use your Mac\'s IP address instead (e.g., http://192.168.1.100:8000)\n   Find your IP: ifconfig | grep "inet " | grep -v 127.0.0.1\n   Then update: import api from \'../services/api\'; api.updateBaseURL(\'http://YOUR_IP:8000\');'
              : '';
            errorMessage = `Network request failed to ${this.baseURL}.\n\nTroubleshooting:\n1. Is the Django server running? (python manage.py runserver 0.0.0.0:8000)\n2. For iOS Simulator: Use http://localhost:8000\n3. For physical device: Use your Mac's IP address${deviceHint}\n4. Check firewall settings\n5. Verify device is on same network\n\nCurrent URL: ${this.baseURL}`;
          } else if (fetchError.message.includes('timeout') || fetchError.message.includes('timed out')) {
            errorMessage = 'Request timed out. The server may be slow or unreachable.';
          } else if (fetchError.message.includes('Failed to fetch') || 
                     fetchError.message.includes('failed to fetch')) {
            errorMessage = `Failed to connect to ${this.baseURL}.\n\nPlease verify:\n- Server is running (check terminal)\n- Correct IP address and port\n- Network connectivity\n- CORS settings allow mobile app\n- Info.plist allows this domain`;
          } else if (fetchError.message.includes('ECONNREFUSED') || 
                     fetchError.message.includes('connection refused')) {
            errorMessage = `Connection refused. Server may not be running at ${this.baseURL}.\n\nStart server with: python manage.py runserver 0.0.0.0:8000`;
          } else {
            errorMessage = `Network error: ${fetchError.message}\n\nURL: ${this.baseURL}`;
          }
        }
        
        return {
          status: 0,
          error: errorMessage,
        };
      }

      console.log(`[API] Response status: ${response.status}`);

      // Handle 403 Forbidden - permission denied
      if (response.status === 403) {
        console.error('[API] 403 Forbidden - Permission denied');
        console.error('[API] Request URL:', url);
        console.error('[API] Request Method:', options.method || 'GET');
        console.error('[API] Has Token:', !!token);
        console.error('[API] Token Preview:', token ? `${token.substring(0, 20)}...` : 'none');
        
        const contentType = response.headers.get('content-type');
        let errorData: any = { detail: 'Permission denied' };
        
        // Read error message from response (clone first to avoid consuming the body)
        if (contentType && contentType.includes('application/json')) {
          try {
            const responseClone = response.clone();
            const text = await responseClone.text();
            console.error('[API] 403 Response Body:', text);
            if (text) {
              errorData = JSON.parse(text);
              console.error('[API] 403 Parsed Error Data:', JSON.stringify(errorData, null, 2));
            }
          } catch (e) {
            console.error('[API] Failed to parse 403 error response:', e);
          }
        } else {
          // Try to read as text anyway
          try {
            const responseClone = response.clone();
            const text = await responseClone.text();
            console.error('[API] 403 Response Body (non-JSON):', text);
            errorData = { detail: text || 'Permission denied' };
          } catch (e) {
            console.error('[API] Failed to read 403 response body:', e);
          }
        }
        
        // Log response headers for debugging
        console.error('[API] 403 Response Headers:');
        try {
          // Headers.forEach may not be available in all React Native environments
          // Use alternative method to iterate headers
          if (response.headers && typeof response.headers.forEach === 'function') {
            response.headers.forEach((value, key) => {
              console.error(`[API]   ${key}: ${value}`);
            });
          } else if (response.headers && typeof response.headers.entries === 'function') {
            // Alternative: use entries() iterator
            for (const [key, value] of response.headers.entries()) {
              console.error(`[API]   ${key}: ${value}`);
            }
          } else {
            // Fallback: try to access common headers directly
            const headersToCheck = ['x-frame-options', 'content-type', 'www-authenticate', 'x-content-type-options'];
            headersToCheck.forEach(headerName => {
              const value = response.headers.get(headerName);
              if (value) {
                console.error(`[API]   ${headerName}: ${value}`);
              }
            });
          }
        } catch (e) {
          console.error('[API] Error logging headers:', e);
        }
        
        // If we have a token but got 403, it might be expired or invalid
        if (token) {
          console.log('[API] Token present but 403 received - token may be invalid or expired');
          console.log('[API] Attempting token refresh...');
          // Try to refresh token
          const refreshed = await this.refreshAccessToken();
          if (refreshed) {
            console.log('[API] Token refresh successful, retrying request...');
            const newToken = await this.getToken();
            if (newToken) {
              headers['Authorization'] = `Bearer ${newToken}`;
              // Retry the request once
              response = await fetch(url, {
                ...options,
                headers,
              });
              console.log('[API] Retry response status:', response.status);
              // If still 403 after refresh, return error with detailed info
              if (response.status === 403) {
                const retryErrorData: any = { detail: 'Permission denied after token refresh' };
                try {
                  const retryText = await response.clone().text();
                  if (retryText) {
                    retryErrorData.original = JSON.parse(retryText);
                  }
                } catch (e) {
                  // Ignore parse errors
                }
                return {
                  status: 403,
                  error: `Permission denied. ${errorData.detail || errorData.message || 'The server explicitly denied access to this resource. Please check:\n1. Django server logs for the exact permission error\n2. Your user account has the required permissions\n3. The API endpoint URL is correct\n4. Try logging out and logging back in'}`,
                };
              }
              // If retry succeeded, continue with normal processing below
            }
          } else {
            console.error('[API] Token refresh failed');
            // Refresh failed, clear tokens
            await this.clearTokens();
            return {
              status: 403,
              error: 'Session expired. Token refresh failed. Please login again.',
            };
          }
        } else {
          // No token - this endpoint requires authentication
          // Log as warning since this might be expected in some cases (e.g., token expired)
          console.warn('[API] No token present - endpoint requires authentication');
          return {
            status: 403,
            error: errorData.detail || errorData.message || 'Authentication required. Please login.',
          };
        }
      }

      // If unauthorized, try to refresh token
      if (response.status === 401 && token) {
        const refreshed = await this.refreshAccessToken();
        if (refreshed) {
          const newToken = await this.getToken();
          if (newToken) {
            headers['Authorization'] = `Bearer ${newToken}`;
            response = await fetch(url, {
              ...options,
              headers,
            });
            // Check if the retry also failed with 401
            if (response.status === 401) {
              // Refresh failed, clear tokens and return error instead of throwing
              await this.clearTokens();
              return {
                status: 401,
                error: 'Session expired. Please login again.',
              };
            }
          }
        } else {
          // Refresh failed, clear tokens and return error instead of throwing
          await this.clearTokens();
          return {
            status: 401,
            error: 'Session expired. Please login again.',
          };
        }
      }

      let data: any = {};
      const contentType = response.headers.get('content-type');
      
      if (contentType && contentType.includes('application/json')) {
        try {
          const text = await response.text();
          console.log(`[API] Response body: ${text.substring(0, 500)}`);
          data = JSON.parse(text);
        } catch (parseError: any) {
          console.error('[API] JSON parse error:', parseError);
          return {
            status: response.status,
            error: `Invalid response from server: ${parseError.message}`,
          };
        }
      } else {
        const text = await response.text();
        console.log(`[API] Non-JSON response: ${text.substring(0, 500)}`);
        data = { detail: text || 'An error occurred' };
      }

      if (!response.ok) {
        console.error('[API] Error response:', data);
        
        // Handle Django REST Framework validation errors
        let errorMessage = 'An error occurred';
        if (data.detail) {
          errorMessage = data.detail;
        } else if (data.message) {
          errorMessage = data.message;
        } else if (data.error) {
          errorMessage = data.error;
        } else if (typeof data === 'string') {
          errorMessage = data;
        } else if (Array.isArray(data)) {
          errorMessage = data.join(', ');
        } else if (typeof data === 'object') {
          // Handle DRF field-level validation errors
          const fieldErrors = Object.keys(data).map(key => {
            const value = data[key];
            if (Array.isArray(value)) {
              return `${key}: ${value.join(', ')}`;
            }
            return `${key}: ${value}`;
          });
          if (fieldErrors.length > 0) {
            errorMessage = fieldErrors.join('; ');
          }
        }
        
        return {
          status: response.status,
          error: errorMessage,
        };
      }

      return {
        status: response.status,
        data: data as T,
      };
    } catch (error: any) {
      console.error('[API] Request error:', error);
      return {
        status: 0,
        error: error.message || 'Network error. Please check your connection.',
      };
    }
  }

  // Authentication Methods
  async login(usernameOrEmail: string, password: string): Promise<ApiResponse<{ access: string; refresh: string; status?: string; temp_otp_token?: string }>> {
    // Build request body - only include fields that have values
    const isEmail = usernameOrEmail.includes('@');
    const requestBody: any = { password };
    if (isEmail) {
      requestBody.email = usernameOrEmail;
    } else {
      requestBody.username = usernameOrEmail;
    }

    console.log('[API] Login request body:', { ...requestBody, password: '***' });

    const response = await this.makeRequest<{ 
      status: string;
      detail: string;
      jwt?: { access: string; refresh: string };
      access?: string;
      refresh?: string;
      temp_otp_token?: string;
    }>(
      API_ENDPOINTS.AUTH.LOGIN,
      {
        method: 'POST',
        body: JSON.stringify(requestBody),
      }
    );

    console.log('[API] Login response:', response);

    // If there's an error, return it immediately
    if (response.error) {
      return response;
    }

    // Handle successful login without 2FA
    if (response.data && response.data.jwt) {
      await this.setTokens(response.data.jwt.access, response.data.jwt.refresh);
      return {
        status: response.status,
        data: {
          access: response.data.jwt.access,
          refresh: response.data.jwt.refresh,
        },
      };
    }
    
    // Handle successful login with direct access/refresh (fallback)
    if (response.data && response.data.access && response.data.refresh) {
      await this.setTokens(response.data.access, response.data.refresh);
      return {
        status: response.status,
        data: {
          access: response.data.access,
          refresh: response.data.refresh,
        },
      };
    }

    // Handle 2FA required response
    if (response.data && response.data.status === 'otp_required' && response.data.temp_otp_token) {
      return {
        status: response.status,
        data: {
          status: 'otp_required',
          temp_otp_token: response.data.temp_otp_token,
        } as any,
      };
    }

    // If we get here, something unexpected happened
    console.warn('[API] Unexpected login response format:', response);
    return {
      status: response.status,
      error: 'Unexpected response format from server',
    };
  }

  async register(email: string, username: string, password1: string, password2: string): Promise<ApiResponse<any>> {
    return this.makeRequest(
      API_ENDPOINTS.AUTH.REGISTER,
      {
        method: 'POST',
        body: JSON.stringify({ email, username, password1, password2 }),
      }
    );
  }

  async verifyOTP(otp: string, tempOtpToken: string): Promise<ApiResponse<{ access: string; refresh: string }>> {
    const response = await this.makeRequest<{ 
      access: string; 
      refresh: string;
      user?: any;
    }>(
      API_ENDPOINTS.AUTH.VERIFY_OTP,
      {
        method: 'POST',
        body: JSON.stringify({ otp, temp_otp_token: tempOtpToken }),
      }
    );

    if (response.data && response.data.access && response.data.refresh) {
      await this.setTokens(response.data.access, response.data.refresh);
    }

    return response;
  }

  async logout(): Promise<void> {
    await this.makeRequest(API_ENDPOINTS.AUTH.LOGOUT, { method: 'POST' });
    await this.clearTokens();
  }

  async getUserDetails(): Promise<ApiResponse<any>> {
    return this.makeRequest(API_ENDPOINTS.AUTH.USER_DETAILS);
  }

  async verifyToken(token?: string): Promise<ApiResponse<any>> {
    const tokenToVerify = token || await this.getToken();
    if (!tokenToVerify) {
      return {
        status: 400,
        error: 'No token provided',
      };
    }
    return this.makeRequest(API_ENDPOINTS.AUTH.TOKEN_VERIFY, {
      method: 'POST',
      body: JSON.stringify({ token: tokenToVerify }),
    });
  }

  async changePassword(oldPassword: string, newPassword1: string, newPassword2: string): Promise<ApiResponse<any>> {
    return this.makeRequest(
      API_ENDPOINTS.AUTH.PASSWORD_CHANGE,
      {
        method: 'POST',
        body: JSON.stringify({ old_password: oldPassword, new_password1: newPassword1, new_password2: newPassword2 }),
      }
    );
  }

  // Records/F financial Data Methods
  async getInsights(): Promise<ApiResponse<any>> {
    return this.makeRequest(API_ENDPOINTS.RECORDS.INSIGHTS);
  }

  async getExplorer(): Promise<ApiResponse<any>> {
    return this.makeRequest(API_ENDPOINTS.RECORDS.EXPLORER);
  }

  async uploadDocument(formData: FormData): Promise<ApiResponse<any>> {
    const token = await this.getToken();
    const headers: HeadersInit = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${this.baseURL}${API_ENDPOINTS.RECORDS.UPLOAD}`, {
      method: 'POST',
      headers,
      body: formData,
    });

    const data = await response.json().catch(() => ({}));
    return {
      status: response.status,
      data: response.ok ? data : undefined,
      error: response.ok ? undefined : (data.detail || 'Upload failed'),
    };
  }

  async getDocuments(): Promise<ApiResponse<any>> {
    return this.makeRequest(API_ENDPOINTS.RECORDS.DOCUMENTS);
  }

  async deleteDocument(id: number): Promise<ApiResponse<any>> {
    return this.makeRequest(API_ENDPOINTS.RECORDS.DELETE_DOCUMENT(id), {
      method: 'DELETE',
    });
  }

  async getDocumentDetails(id: number): Promise<ApiResponse<any>> {
    return this.makeRequest(API_ENDPOINTS.RECORDS.DOCUMENT_DETAILS(id));
  }

  async getLinkedAccounts(): Promise<ApiResponse<any>> {
    return this.makeRequest(API_ENDPOINTS.RECORDS.LINKED_ACCOUNTS);
  }

  async createLinkToken(): Promise<ApiResponse<any>> {
    return this.makeRequest(API_ENDPOINTS.RECORDS.CREATE_LINK_TOKEN, {
      method: 'POST',
    });
  }

  // Stock Analysis Methods
  async analyzeStock(symbol: string, forecastDays: number = 365, equationType?: string): Promise<ApiResponse<any>> {
    return this.makeRequest(API_ENDPOINTS.STOCK_ANALYSIS.ANALYZE, {
      method: 'POST',
      body: JSON.stringify({ symbol, forecast_days: forecastDays, equation_type: equationType }),
    });
  }

  async getStockDetails(symbol: string): Promise<ApiResponse<StockDetailsResponse>> {
    return this.makeRequest(API_ENDPOINTS.STOCK_ANALYSIS.DETAILS, {
      method: 'POST',
      body: JSON.stringify({ symbol }),
    });
  }

  async getAnalysisResults(id: number): Promise<ApiResponse<any>> {
    return this.makeRequest(API_ENDPOINTS.STOCK_ANALYSIS.RESULTS(id));
  }

  // Dashboard Methods
  async getDashboardStats(): Promise<ApiResponse<any>> {
    return this.makeRequest(API_ENDPOINTS.DASHBOARD.STATS);
  }

  // Subscription Methods
  async getSubscriptionPlans(): Promise<ApiResponse<any>> {
    return this.makeRequest(API_ENDPOINTS.SUBSCRIPTIONS.PLANS);
  }

  async getCurrentSubscription(): Promise<ApiResponse<any>> {
    return this.makeRequest(API_ENDPOINTS.SUBSCRIPTIONS.CURRENT);
  }

  // User Profile Methods
  async getUserProfile(): Promise<ApiResponse<any>> {
    return this.makeRequest(API_ENDPOINTS.USERS.PROFILE);
  }

  async updateProfile(data: {
    first_name?: string;
    last_name?: string;
    email?: string;
    language?: string;
    timezone?: string;
  }): Promise<ApiResponse<any>> {
    return this.makeRequest(API_ENDPOINTS.USERS.PROFILE, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  // Chat Methods
  async startChat(): Promise<ApiResponse<any>> {
    return this.makeRequest(API_ENDPOINTS.CHAT.START, {
      method: 'POST',
    });
  }

  async getChat(chatId: number): Promise<ApiResponse<any>> {
    return this.makeRequest(API_ENDPOINTS.CHAT.SINGLE(chatId));
  }

  async sendChatMessage(chatId: number, message: string): Promise<ApiResponse<any>> {
    return this.makeRequest(API_ENDPOINTS.CHAT.NEW_MESSAGE(chatId), {
      method: 'POST',
      body: JSON.stringify({
        chat: chatId,
        message_type: 'HUMAN',
        content: message,
      }),
    });
  }

  async getChatResponse(chatId: number, taskId: string): Promise<ApiResponse<any>> {
    return this.makeRequest(API_ENDPOINTS.CHAT.GET_RESPONSE(chatId, taskId));
  }

  async clearChatHistory(chatId: number): Promise<ApiResponse<any>> {
    return this.makeRequest(API_ENDPOINTS.CHAT.CLEAR_HISTORY(chatId), {
      method: 'POST',
    });
  }

  async getChatUserData(): Promise<ApiResponse<any>> {
    return this.makeRequest(API_ENDPOINTS.CHAT.USER_DATA);
  }

  // Financial Aggregation Methods
  async getDashboardSummary(): Promise<ApiResponse<any>> {
    return this.makeRequest(API_ENDPOINTS.FINANCIAL.DASHBOARD_SUMMARY);
  }

  async getBudgetData(days: number = 30): Promise<ApiResponse<any>> {
    return this.makeRequest(`${API_ENDPOINTS.FINANCIAL.BUDGET_DATA}?days=${days}`);
  }

  async getInvestmentData(): Promise<ApiResponse<any>> {
    return this.makeRequest(API_ENDPOINTS.FINANCIAL.INVESTMENT_DATA);
  }

  async getDebtData(): Promise<ApiResponse<any>> {
    return this.makeRequest(API_ENDPOINTS.FINANCIAL.DEBT_DATA);
  }

  async getAccountDetail(accountId: number): Promise<ApiResponse<any>> {
    return this.makeRequest(API_ENDPOINTS.RECORDS.ACCOUNT_DETAIL(accountId));
  }

  async syncAccount(accountId: number): Promise<ApiResponse<any>> {
    return this.makeRequest(API_ENDPOINTS.RECORDS.SYNC_ACCOUNT(accountId), {
      method: 'POST',
    });
  }

  async disconnectAccount(accountId: number): Promise<ApiResponse<any>> {
    return this.makeRequest(API_ENDPOINTS.RECORDS.DISCONNECT_ACCOUNT(accountId), {
      method: 'POST',
    });
  }

  // Watchlist Methods
  async getWatchlist(): Promise<ApiResponse<any>> {
    return this.makeRequest(API_ENDPOINTS.INVESTMENT_SAVINGS.WATCHLIST);
  }

  async addToWatchlist(symbol: string, nickname?: string, notes?: string): Promise<ApiResponse<any>> {
    return this.makeRequest(API_ENDPOINTS.INVESTMENT_SAVINGS.WATCHLIST_ADD, {
      method: 'POST',
      body: JSON.stringify({ symbol, nickname, notes }),
    });
  }

  async removeFromWatchlist(entryId: number): Promise<ApiResponse<any>> {
    return this.makeRequest(API_ENDPOINTS.INVESTMENT_SAVINGS.WATCHLIST_REMOVE(entryId), {
      method: 'POST',
    });
  }

  async refreshWatchlist(entryId: number): Promise<ApiResponse<any>> {
    return this.makeRequest(API_ENDPOINTS.INVESTMENT_SAVINGS.WATCHLIST_REFRESH(entryId), {
      method: 'POST',
    });
  }

  // Investment & Savings Assessment Methods
  async getInvestmentSavingsSummary(): Promise<ApiResponse<any>> {
    return this.makeRequest(API_ENDPOINTS.INVESTMENT_SAVINGS.SUMMARY);
  }

  async getStocksAssessments(): Promise<ApiResponse<any>> {
    return this.makeRequest(API_ENDPOINTS.INVESTMENT_SAVINGS.STOCKS_ASSESSMENT);
  }

  async getSavingsAssessments(): Promise<ApiResponse<any>> {
    return this.makeRequest(API_ENDPOINTS.INVESTMENT_SAVINGS.SAVINGS_ASSESSMENT);
  }

  async getCDAssessments(): Promise<ApiResponse<any>> {
    return this.makeRequest(API_ENDPOINTS.INVESTMENT_SAVINGS.CD_ASSESSMENT);
  }

  async getBondAssessments(): Promise<ApiResponse<any>> {
    return this.makeRequest(API_ENDPOINTS.INVESTMENT_SAVINGS.BOND_ASSESSMENT);
  }

  async saveStocksAssessment(data: {
    symbol: string;
    investment_amount?: number;
    share_quantity?: number;
    current_price: number;
    forecast_data?: any;
    notes?: string;
    linked_account_id?: number;
  }): Promise<ApiResponse<any>> {
    return this.makeRequest(API_ENDPOINTS.INVESTMENT_SAVINGS.SAVE_STOCKS, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async saveSavingsAssessment(data: {
    account_name?: string;
    initial_deposit: number;
    annual_interest_rate: number;
    monthly_contribution?: number;
    biweekly_contribution?: number;
    compounding_frequency?: number;
    forecast_data?: any;
    notes?: string;
    linked_account_id?: number;
    id?: number;
  }): Promise<ApiResponse<any>> {
    return this.makeRequest(API_ENDPOINTS.INVESTMENT_SAVINGS.SAVE_SAVINGS, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async saveCDAssessment(data: {
    account_name?: string;
    amount: number;
    annual_interest_rate: number;
    term_months: number;
    compounding_frequency?: number;
    forecast_data?: any;
    notes?: string;
    linked_account_id?: number;
    id?: number;
  }): Promise<ApiResponse<any>> {
    return this.makeRequest(API_ENDPOINTS.INVESTMENT_SAVINGS.SAVE_CD, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async saveBondAssessment(data: {
    account_name?: string;
    face_value: number;
    coupon_rate: number;
    purchase_price: number;
    years_to_maturity: number;
    payment_frequency?: number;
    forecast_data?: any;
    notes?: string;
    linked_account_id?: number;
    id?: number;
  }): Promise<ApiResponse<any>> {
    return this.makeRequest(API_ENDPOINTS.INVESTMENT_SAVINGS.SAVE_BOND, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getStocksAssessmentDetail(pk: number): Promise<ApiResponse<any>> {
    return this.makeRequest(`${API_ENDPOINTS.INVESTMENT_SAVINGS.STOCKS_ASSESSMENT}${pk}/`);
  }
}

export default new ApiService();
