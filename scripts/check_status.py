import sys
sys.path.insert(0, 'src')
from connectors.mt5_connector import MT5Connector

connector = MT5Connector('check')
if connector.connect(5043091442, 'Mq*y6BFJ', 'MetaQuotes-Demo'):
    positions = connector.get_positions()
    if positions:
        print(f'{len(positions)} Open Positions:')
        total_profit = sum(p.profit for p in positions)
        for pos in positions:
            print(f'  {pos.symbol}: {pos.type.name} {pos.volume} lots @ P/L: ${pos.profit:.2f}')
        print(f'\nTotal P/L: ${total_profit:.2f}')
        print(f'Target: $100.00 ({total_profit/100*100:.1f}% complete)')
    else:
        print('No open positions')
    connector.disconnect()
