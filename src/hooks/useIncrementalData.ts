import { useState, useCallback, useRef } from 'react';
import type { Position } from '@/types/trading';

interface CachedData<T> {
  data: T;
  timestamp: number;
  lastId?: number;
}

const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes for closed positions

export function useIncrementalData() {
  const closedPositionsCache = useRef<CachedData<Position[]>>({
    data: [],
    timestamp: 0,
    lastId: 0,
  });

  const isValidCache = useCallback((cache: CachedData<any>): boolean => {
    return Date.now() - cache.timestamp < CACHE_DURATION;
  }, []);

  /**
   * Get closed positions incrementally - only fetch new ones since last update
   */
  const getClosedPositionsIncremental = useCallback(
    async (
      fetchFn: (params: { after_id?: number; limit?: number }) => Promise<any[]>
    ): Promise<Position[]> => {
      try {
        // If cache is still valid, return cached data
        if (isValidCache(closedPositionsCache.current)) {
          return closedPositionsCache.current.data;
        }

        // Fetch only new closed positions since last fetch
        const lastId = closedPositionsCache.current.lastId;
        const apiData = await fetchFn({
          after_id: lastId,
          limit: 100,
        });

        if (apiData.length > 0) {
          // Convert API data to Position type
          const newPositions: Position[] = apiData
            .filter((p: any) => p.close_time || p.time_close)
            .map((p: any) => ({
              ticket: p.ticket,
              symbol: p.symbol,
              type: p.type?.toLowerCase() as "buy" | "sell",
              volume: p.volume,
              openPrice: p.price_open || p.open_price,
              currentPrice: p.price_current || p.current_price || p.close_price,
              sl: p.sl || null,
              tp: p.tp || null,
              profit: p.profit || 0,
              openTime: p.open_time || p.time_open,
              closeTime: p.close_time || p.time_close,
              account_id: p.account_id,
            }));

          // Merge new positions with existing cache
          const allPositions = [...newPositions, ...closedPositionsCache.current.data];
          
          // Sort by close time descending and remove duplicates
          const uniquePositions = Array.from(
            new Map(allPositions.map(p => [p.ticket, p])).values()
          ).sort((a, b) => {
            const aTime = new Date(a.closeTime || 0).getTime();
            const bTime = new Date(b.closeTime || 0).getTime();
            return bTime - aTime;
          });

          // Update cache
          closedPositionsCache.current = {
            data: uniquePositions,
            timestamp: Date.now(),
            lastId: Math.max(...uniquePositions.map(p => p.ticket)),
          };

          return uniquePositions;
        }

        // No new positions, return existing cache
        return closedPositionsCache.current.data;
      } catch (error) {
        console.error('Failed to fetch incremental closed positions:', error);
        return closedPositionsCache.current.data;
      }
    },
    [isValidCache]
  );

  /**
   * Add a newly closed position to the cache
   */
  const addClosedPosition = useCallback((position: Position) => {
    const cache = closedPositionsCache.current;
    
    // Check if position already exists
    const exists = cache.data.some(p => p.ticket === position.ticket);
    if (exists) return;

    // Add to cache
    const updatedData = [position, ...cache.data].sort((a, b) => {
      const aTime = new Date(a.closeTime || 0).getTime();
      const bTime = new Date(b.closeTime || 0).getTime();
      return bTime - aTime;
    });

    closedPositionsCache.current = {
      data: updatedData,
      timestamp: Date.now(),
      lastId: Math.max(cache.lastId || 0, position.ticket),
    };
  }, []);

  /**
   * Invalidate cache to force full refresh
   */
  const invalidateCache = useCallback(() => {
    closedPositionsCache.current = {
      data: [],
      timestamp: 0,
      lastId: 0,
    };
  }, []);

  /**
   * Clear old cached data to prevent memory leaks
   */
  const clearOldCache = useCallback((maxAge: number = CACHE_DURATION * 2) => {
    const now = Date.now();
    const cache = closedPositionsCache.current;
    
    if (now - cache.timestamp > maxAge) {
      invalidateCache();
    }
  }, [invalidateCache]);

  return {
    getClosedPositionsIncremental,
    addClosedPosition,
    invalidateCache,
    clearOldCache,
    getCachedClosedPositions: () => closedPositionsCache.current.data,
  };
}
