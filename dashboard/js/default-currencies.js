/**
 * Default Trading Currencies
 * Common forex pairs, commodities, and indices
 */

const DEFAULT_CURRENCIES = {
    // Major Forex Pairs
    forex_majors: [
        {
            symbol: 'EURUSD',
            description: 'Euro vs US Dollar',
            category: 'Forex Majors',
            digits: 5,
            point: 0.00001,
            contract_size: 100000,
            min_lot: 0.01,
            max_lot: 100.0,
            lot_step: 0.01,
            spread_typical: 1.5,
            enabled: true
        },
        {
            symbol: 'GBPUSD',
            description: 'British Pound vs US Dollar',
            category: 'Forex Majors',
            digits: 5,
            point: 0.00001,
            contract_size: 100000,
            min_lot: 0.01,
            max_lot: 100.0,
            lot_step: 0.01,
            spread_typical: 2.0,
            enabled: true
        },
        {
            symbol: 'USDJPY',
            description: 'US Dollar vs Japanese Yen',
            category: 'Forex Majors',
            digits: 3,
            point: 0.001,
            contract_size: 100000,
            min_lot: 0.01,
            max_lot: 100.0,
            lot_step: 0.01,
            spread_typical: 1.5,
            enabled: true
        },
        {
            symbol: 'USDCHF',
            description: 'US Dollar vs Swiss Franc',
            category: 'Forex Majors',
            digits: 5,
            point: 0.00001,
            contract_size: 100000,
            min_lot: 0.01,
            max_lot: 100.0,
            lot_step: 0.01,
            spread_typical: 2.0,
            enabled: true
        }
    ],

    // Minor Forex Pairs
    forex_minors: [
        {
            symbol: 'AUDUSD',
            description: 'Australian Dollar vs US Dollar',
            category: 'Forex Minors',
            digits: 5,
            point: 0.00001,
            contract_size: 100000,
            min_lot: 0.01,
            max_lot: 100.0,
            lot_step: 0.01,
            spread_typical: 2.0,
            enabled: true
        },
        {
            symbol: 'USDCAD',
            description: 'US Dollar vs Canadian Dollar',
            category: 'Forex Minors',
            digits: 5,
            point: 0.00001,
            contract_size: 100000,
            min_lot: 0.01,
            max_lot: 100.0,
            lot_step: 0.01,
            spread_typical: 2.5,
            enabled: true
        },
        {
            symbol: 'NZDUSD',
            description: 'New Zealand Dollar vs US Dollar',
            category: 'Forex Minors',
            digits: 5,
            point: 0.00001,
            contract_size: 100000,
            min_lot: 0.01,
            max_lot: 100.0,
            lot_step: 0.01,
            spread_typical: 2.5,
            enabled: true
        },
        {
            symbol: 'EURGBP',
            description: 'Euro vs British Pound',
            category: 'Forex Minors',
            digits: 5,
            point: 0.00001,
            contract_size: 100000,
            min_lot: 0.01,
            max_lot: 100.0,
            lot_step: 0.01,
            spread_typical: 2.0,
            enabled: true
        },
        {
            symbol: 'EURJPY',
            description: 'Euro vs Japanese Yen',
            category: 'Forex Minors',
            digits: 3,
            point: 0.001,
            contract_size: 100000,
            min_lot: 0.01,
            max_lot: 100.0,
            lot_step: 0.01,
            spread_typical: 2.0,
            enabled: true
        },
        {
            symbol: 'GBPJPY',
            description: 'British Pound vs Japanese Yen',
            category: 'Forex Minors',
            digits: 3,
            point: 0.001,
            contract_size: 100000,
            min_lot: 0.01,
            max_lot: 100.0,
            lot_step: 0.01,
            spread_typical: 3.0,
            enabled: true
        }
    ],

    // Commodities
    commodities: [
        {
            symbol: 'XAUUSD',
            description: 'Gold vs US Dollar',
            category: 'Commodities',
            digits: 2,
            point: 0.01,
            contract_size: 100,
            min_lot: 0.01,
            max_lot: 100.0,
            lot_step: 0.01,
            spread_typical: 30,
            enabled: true
        },
        {
            symbol: 'XAGUSD',
            description: 'Silver vs US Dollar',
            category: 'Commodities',
            digits: 3,
            point: 0.001,
            contract_size: 5000,
            min_lot: 0.01,
            max_lot: 100.0,
            lot_step: 0.01,
            spread_typical: 30,
            enabled: true
        },
        {
            symbol: 'XTIUSD',
            description: 'WTI Crude Oil',
            category: 'Commodities',
            digits: 2,
            point: 0.01,
            contract_size: 1000,
            min_lot: 0.01,
            max_lot: 100.0,
            lot_step: 0.01,
            spread_typical: 30,
            enabled: true
        },
        {
            symbol: 'XBRUSD',
            description: 'Brent Crude Oil',
            category: 'Commodities',
            digits: 2,
            point: 0.01,
            contract_size: 1000,
            min_lot: 0.01,
            max_lot: 100.0,
            lot_step: 0.01,
            spread_typical: 30,
            enabled: true
        }
    ],

    // Indices
    indices: [
        {
            symbol: 'US30',
            description: 'Dow Jones Industrial Average',
            category: 'Indices',
            digits: 2,
            point: 0.01,
            contract_size: 1,
            min_lot: 0.01,
            max_lot: 100.0,
            lot_step: 0.01,
            spread_typical: 5,
            enabled: true
        },
        {
            symbol: 'US500',
            description: 'S&P 500',
            category: 'Indices',
            digits: 2,
            point: 0.01,
            contract_size: 1,
            min_lot: 0.01,
            max_lot: 100.0,
            lot_step: 0.01,
            spread_typical: 5,
            enabled: true
        },
        {
            symbol: 'NAS100',
            description: 'NASDAQ 100',
            category: 'Indices',
            digits: 2,
            point: 0.01,
            contract_size: 1,
            min_lot: 0.01,
            max_lot: 100.0,
            lot_step: 0.01,
            spread_typical: 5,
            enabled: true
        },
        {
            symbol: 'GER40',
            description: 'German DAX',
            category: 'Indices',
            digits: 2,
            point: 0.01,
            contract_size: 1,
            min_lot: 0.01,
            max_lot: 100.0,
            lot_step: 0.01,
            spread_typical: 5,
            enabled: true
        }
    ],

    // Cryptocurrencies
    crypto: [
        {
            symbol: 'BTCUSD',
            description: 'Bitcoin vs US Dollar',
            category: 'Crypto',
            digits: 2,
            point: 0.01,
            contract_size: 1,
            min_lot: 0.01,
            max_lot: 10.0,
            lot_step: 0.01,
            spread_typical: 50,
            enabled: false  // Disabled by default, user can enable
        },
        {
            symbol: 'ETHUSD',
            description: 'Ethereum vs US Dollar',
            category: 'Crypto',
            digits: 2,
            point: 0.01,
            contract_size: 1,
            min_lot: 0.01,
            max_lot: 10.0,
            lot_step: 0.01,
            spread_typical: 50,
            enabled: false  // Disabled by default, user can enable
        }
    ]
};

/**
 * Get all default currencies as a flat array
 */
function getAllDefaultCurrencies() {
    return [
        ...DEFAULT_CURRENCIES.forex_majors,
        ...DEFAULT_CURRENCIES.forex_minors,
        ...DEFAULT_CURRENCIES.commodities,
        ...DEFAULT_CURRENCIES.indices,
        ...DEFAULT_CURRENCIES.crypto
    ];
}

/**
 * Get only enabled default currencies
 */
function getEnabledDefaultCurrencies() {
    return getAllDefaultCurrencies().filter(c => c.enabled);
}

/**
 * Get default currencies by category
 */
function getDefaultCurrenciesByCategory(category) {
    switch (category.toLowerCase()) {
        case 'forex majors':
            return DEFAULT_CURRENCIES.forex_majors;
        case 'forex minors':
            return DEFAULT_CURRENCIES.forex_minors;
        case 'commodities':
            return DEFAULT_CURRENCIES.commodities;
        case 'indices':
            return DEFAULT_CURRENCIES.indices;
        case 'crypto':
            return DEFAULT_CURRENCIES.crypto;
        default:
            return [];
    }
}

/**
 * Get default currency by symbol
 */
function getDefaultCurrency(symbol) {
    return getAllDefaultCurrencies().find(c => c.symbol === symbol);
}

/**
 * Get categories
 */
function getDefaultCurrencyCategories() {
    return [
        { name: 'Forex Majors', count: DEFAULT_CURRENCIES.forex_majors.length },
        { name: 'Forex Minors', count: DEFAULT_CURRENCIES.forex_minors.length },
        { name: 'Commodities', count: DEFAULT_CURRENCIES.commodities.length },
        { name: 'Indices', count: DEFAULT_CURRENCIES.indices.length },
        { name: 'Crypto', count: DEFAULT_CURRENCIES.crypto.length }
    ];
}

// Export for use in other modules
if (typeof window !== 'undefined') {
    window.DEFAULT_CURRENCIES = DEFAULT_CURRENCIES;
    window.getAllDefaultCurrencies = getAllDefaultCurrencies;
    window.getEnabledDefaultCurrencies = getEnabledDefaultCurrencies;
    window.getDefaultCurrenciesByCategory = getDefaultCurrenciesByCategory;
    window.getDefaultCurrency = getDefaultCurrency;
    window.getDefaultCurrencyCategories = getDefaultCurrencyCategories;
}
