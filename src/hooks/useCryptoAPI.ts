/**
 * Crypto API Hook
 *
 * Custom hook for making API calls to crypto trading endpoints.
 * Uses React Query for caching and state management.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type {
  CryptoAccount,
  PositionSummary,
  CryptoOrder,
  OrderListResponse,
  MarketTicker,
  PortfolioSummary,
  PerformanceMetrics,
  CreateAccountRequest,
  UpdateAccountRequest,
  PlaceOrderRequest,
  Exchange,
  Symbol,
} from '@/types/crypto';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// ===========================================================================
// API Functions
// ===========================================================================

// Accounts
async function fetchCryptoAccounts(): Promise<CryptoAccount[]> {
  const response = await fetch(`${API_BASE_URL}/api/v2/accounts/crypto`);
  if (!response.ok) throw new Error('Failed to fetch crypto accounts');
  return response.json();
}

async function fetchCryptoAccount(accountId: number): Promise<CryptoAccount> {
  const response = await fetch(`${API_BASE_URL}/api/v2/accounts/${accountId}/crypto`);
  if (!response.ok) throw new Error('Failed to fetch crypto account');
  return response.json();
}

async function createCryptoAccount(data: CreateAccountRequest): Promise<CryptoAccount> {
  const response = await fetch(`${API_BASE_URL}/api/v2/accounts/crypto`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to create crypto account');
  }
  return response.json();
}

async function updateCryptoAccount(accountId: number, data: UpdateAccountRequest): Promise<CryptoAccount> {
  const response = await fetch(`${API_BASE_URL}/api/v2/accounts/${accountId}/crypto`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to update crypto account');
  }
  return response.json();
}

async function deleteCryptoAccount(accountId: number): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/v2/accounts/${accountId}/crypto`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to delete crypto account');
  }
}

// Positions
async function fetchPositions(accountId: number): Promise<PositionSummary> {
  const response = await fetch(`${API_BASE_URL}/api/v2/accounts/${accountId}/crypto/positions`);
  if (!response.ok) throw new Error('Failed to fetch positions');
  return response.json();
}

async function fetchPositionBySymbol(accountId: number, symbol: string) {
  const response = await fetch(`${API_BASE_URL}/api/v2/accounts/${accountId}/crypto/positions/${symbol}`);
  if (!response.ok) throw new Error('Failed to fetch position');
  return response.json();
}

// Orders
async function placeOrder(accountId: number, data: PlaceOrderRequest): Promise<CryptoOrder> {
  const response = await fetch(`${API_BASE_URL}/api/v2/accounts/${accountId}/crypto/orders`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to place order');
  }
  return response.json();
}

async function fetchOrders(accountId: number, symbol?: string, status?: string): Promise<OrderListResponse> {
  const params = new URLSearchParams();
  if (symbol) params.append('symbol', symbol);
  if (status) params.append('status_filter', status);

  const response = await fetch(
    `${API_BASE_URL}/api/v2/accounts/${accountId}/crypto/orders?${params.toString()}`
  );
  if (!response.ok) throw new Error('Failed to fetch orders');
  return response.json();
}

async function fetchOrder(accountId: number, orderId: string): Promise<CryptoOrder> {
  const response = await fetch(`${API_BASE_URL}/api/v2/accounts/${accountId}/crypto/orders/${orderId}`);
  if (!response.ok) throw new Error('Failed to fetch order');
  return response.json();
}

async function cancelOrder(accountId: number, orderId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/v2/accounts/${accountId}/crypto/orders/${orderId}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to cancel order');
  }
}

// Market Data
async function fetchMarketTicker(symbol: string, exchange: string = 'BINANCE'): Promise<MarketTicker> {
  const response = await fetch(`${API_BASE_URL}/api/v2/crypto/markets/${symbol}?exchange=${exchange}`);
  if (!response.ok) throw new Error('Failed to fetch market ticker');
  return response.json();
}

async function fetchExchanges(): Promise<{ total_exchanges: number; exchanges: Exchange[] }> {
  const response = await fetch(`${API_BASE_URL}/api/v2/crypto/exchanges`);
  if (!response.ok) throw new Error('Failed to fetch exchanges');
  return response.json();
}

async function fetchSymbols(exchange: string = 'BINANCE', quoteAsset?: string) {
  const params = new URLSearchParams({ exchange });
  if (quoteAsset) params.append('quote_asset', quoteAsset);

  const response = await fetch(`${API_BASE_URL}/api/v2/crypto/symbols?${params.toString()}`);
  if (!response.ok) throw new Error('Failed to fetch symbols');
  return response.json();
}

// Analytics
async function fetchPortfolioSummary(accountId: number): Promise<PortfolioSummary> {
  const response = await fetch(`${API_BASE_URL}/api/v2/accounts/${accountId}/crypto/analytics`);
  if (!response.ok) throw new Error('Failed to fetch portfolio summary');
  return response.json();
}

async function fetchPerformanceMetrics(
  accountId: number,
  period: 'daily' | 'weekly' | 'monthly' = 'monthly'
): Promise<PerformanceMetrics> {
  const response = await fetch(
    `${API_BASE_URL}/api/v2/accounts/${accountId}/crypto/analytics/performance?period=${period}`
  );
  if (!response.ok) throw new Error('Failed to fetch performance metrics');
  return response.json();
}

// ===========================================================================
// React Query Hooks
// ===========================================================================

export function useCryptoAccounts() {
  return useQuery({
    queryKey: ['crypto', 'accounts'],
    queryFn: fetchCryptoAccounts,
    staleTime: 30000, // 30 seconds
  });
}

export function useCryptoAccount(accountId: number) {
  return useQuery({
    queryKey: ['crypto', 'accounts', accountId],
    queryFn: () => fetchCryptoAccount(accountId),
    enabled: !!accountId,
    staleTime: 10000, // 10 seconds
  });
}

export function useCreateCryptoAccount() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createCryptoAccount,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['crypto', 'accounts'] });
    },
  });
}

export function useUpdateCryptoAccount(accountId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: UpdateAccountRequest) => updateCryptoAccount(accountId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['crypto', 'accounts'] });
      queryClient.invalidateQueries({ queryKey: ['crypto', 'accounts', accountId] });
    },
  });
}

export function useDeleteCryptoAccount() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deleteCryptoAccount,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['crypto', 'accounts'] });
    },
  });
}

export function usePositions(accountId: number, refreshInterval?: number) {
  return useQuery({
    queryKey: ['crypto', 'positions', accountId],
    queryFn: () => fetchPositions(accountId),
    enabled: !!accountId,
    refetchInterval: refreshInterval || 5000, // Default 5 seconds
    staleTime: 2000, // 2 seconds
  });
}

export function usePlaceOrder(accountId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: PlaceOrderRequest) => placeOrder(accountId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['crypto', 'positions', accountId] });
      queryClient.invalidateQueries({ queryKey: ['crypto', 'orders', accountId] });
    },
  });
}

export function useOrders(accountId: number, symbol?: string, status?: string) {
  return useQuery({
    queryKey: ['crypto', 'orders', accountId, symbol, status],
    queryFn: () => fetchOrders(accountId, symbol, status),
    enabled: !!accountId,
    staleTime: 5000, // 5 seconds
  });
}

export function useCancelOrder(accountId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (orderId: string) => cancelOrder(accountId, orderId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['crypto', 'orders', accountId] });
      queryClient.invalidateQueries({ queryKey: ['crypto', 'positions', accountId] });
    },
  });
}

export function useMarketTicker(symbol: string, exchange: string = 'BINANCE') {
  return useQuery({
    queryKey: ['crypto', 'market', symbol, exchange],
    queryFn: () => fetchMarketTicker(symbol, exchange),
    enabled: !!symbol,
    refetchInterval: 2000, // 2 seconds for real-time feel
    staleTime: 1000, // 1 second
  });
}

export function useExchanges() {
  return useQuery({
    queryKey: ['crypto', 'exchanges'],
    queryFn: fetchExchanges,
    staleTime: 3600000, // 1 hour (rarely changes)
  });
}

export function useSymbols(exchange: string = 'BINANCE', quoteAsset?: string) {
  return useQuery({
    queryKey: ['crypto', 'symbols', exchange, quoteAsset],
    queryFn: () => fetchSymbols(exchange, quoteAsset),
    staleTime: 300000, // 5 minutes
  });
}

export function usePortfolioSummary(accountId: number) {
  return useQuery({
    queryKey: ['crypto', 'analytics', 'portfolio', accountId],
    queryFn: () => fetchPortfolioSummary(accountId),
    enabled: !!accountId,
    refetchInterval: 10000, // 10 seconds
    staleTime: 5000, // 5 seconds
  });
}

export function usePerformanceMetrics(accountId: number, period: 'daily' | 'weekly' | 'monthly' = 'monthly') {
  return useQuery({
    queryKey: ['crypto', 'analytics', 'performance', accountId, period],
    queryFn: () => fetchPerformanceMetrics(accountId, period),
    enabled: !!accountId,
    staleTime: 30000, // 30 seconds
  });
}
