import AsyncStorage from '@react-native-async-storage/async-storage';
import { API_BASE_URL, API_ENDPOINTS } from '../config/api';

const TOKEN_KEY = 'accessToken';
const REFRESH_TOKEN_KEY = 'refreshToken';

export interface ApiResponse<T> {
  data?: T;
  error?: string;
  status: number;
}

class ApiService {
  private baseURL: string;
  private refreshTokenPromise: Promise<boolean> | null = null;
  private isRefreshing: boolean = false;

  constructor() {
    this.baseURL = API_BASE_URL;
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
        ...options.headers,
      };

      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const url = `${this.baseURL}${endpoint}`;
      console.log(`[API] Making request to: ${url}`);
      console.log(`[API] Method: ${options.method || 'GET'}`);

      let response: Response;
      try {
        response = await fetch(url, {
          ...options,
          headers,
        });
      } catch (fetchError: any) {
        console.error('[API] Fetch error:', fetchError);
        
        // Provide more specific error messages based on error type
        let errorMessage = 'Unable to connect to server.';
        if (fetchError.message) {
          if (fetchError.message.includes('Network request failed')) {
            errorMessage = `Network request failed. Please check:\n- Server is running at ${this.baseURL}\n- Your device is on the same network\n- Firewall allows connections to port 8000`;
          } else if (fetchError.message.includes('timeout')) {
            errorMessage = 'Request timed out. The server may be slow or unreachable.';
          } else if (fetchError.message.includes('Failed to fetch')) {
            errorMessage = `Failed to connect to ${this.baseURL}. Please verify:\n- Server is running\n- Correct IP address and port\n- Network connectivity`;
          } else {
            errorMessage = `Network error: ${fetchError.message}`;
          }
        }
        
        return {
          status: 0,
          error: errorMessage,
        };
      }

      console.log(`[API] Response status: ${response.status}`);

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

  async updateProfile(data: any): Promise<ApiResponse<any>> {
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

  // Investment & Savings Methods
  async getInvestmentSavingsSummary(): Promise<ApiResponse<any>> {
    return this.makeRequest(API_ENDPOINTS.INVESTMENT_SAVINGS.SUMMARY);
  }

  async saveStocksAssessment(data: any): Promise<ApiResponse<any>> {
    return this.makeRequest(API_ENDPOINTS.INVESTMENT_SAVINGS.SAVE_STOCKS, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async saveSavingsAssessment(data: any): Promise<ApiResponse<any>> {
    return this.makeRequest(API_ENDPOINTS.INVESTMENT_SAVINGS.SAVE_SAVINGS, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async saveCDAssessment(data: any): Promise<ApiResponse<any>> {
    return this.makeRequest(API_ENDPOINTS.INVESTMENT_SAVINGS.SAVE_CD, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async saveBondAssessment(data: any): Promise<ApiResponse<any>> {
    return this.makeRequest(API_ENDPOINTS.INVESTMENT_SAVINGS.SAVE_BOND, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // Budget Planner Methods
  async getBudgetPlannerData(): Promise<ApiResponse<any>> {
    return this.makeRequest(API_ENDPOINTS.BUDGET_PLANNER);
  }

  // Loan Analysis Methods
  async getLoanResults(id: number): Promise<ApiResponse<any>> {
    return this.makeRequest(API_ENDPOINTS.STOCK_ANALYSIS.LOAN_RESULTS(id));
  }

  // Investment Planner Methods
  async getInvestmentPlanner(analysisPk: number): Promise<ApiResponse<any>> {
    return this.makeRequest(API_ENDPOINTS.STOCK_ANALYSIS.PLANNER(analysisPk));
  }

  async createInvestmentPlan(analysisPk: number, data: any): Promise<ApiResponse<any>> {
    return this.makeRequest(API_ENDPOINTS.STOCK_ANALYSIS.PLANNER(analysisPk), {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }
}

export default new ApiService();

