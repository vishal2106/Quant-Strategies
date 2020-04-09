from quantopian.algorithm import order_optimal_portfolio
from quantopian.algorithm import attach_pipeline, pipeline_output
from quantopian.pipeline import Pipeline
from quantopian.pipeline.data.builtin import USEquityPricing
from quantopian.pipeline.factors import SimpleMovingAverage
from quantopian.pipeline.filters import QTradableStocksUS
import quantopian.optimize as opt

def initialize(context):
    schedule_function(
        my_rebalance,
        date_rules.week_start(),
        time_rules.market_open()
        )
    
    my_pipe = make_pipeline()
    attach_pipeline(my_pipe, 'my_pipeline')
    
def make_pipeline():
    
    base_universe = QTradableStocksUS()
    
    mean_10 = SimpleMovingAverage(
        inputs = [USEquityPricing.close],
        window_length = 10,
        mask = base_universe
        )
    
    mean_30 = SimpleMovingAverage(
        inputs = [USEquityPricing.close],
        window_length = 30,
        mask = base_universe
        )
    
    percent_difference = (mean_10 - mean_30)/(mean_30)
    
    shorts = percent_difference.top(75)
    longs = percent_difference.bottom(75)
    
    securities_to_trade = (shorts | longs)
    
    return Pipeline(
        columns={
            'longs':longs,
            'shorts':shorts
            },
            screen = (securities_to_trade)
        )

def compute_target_weights(context, data):
    
    weights = {}
    
    if context.longs and context.shorts :
        long_weight = 0.5 / len(context.longs)
        short_weight = 0.5 / len(context.shorts)
        
    else:
        return weights
    
    for security in context.portfolio.positions:
        if security not in context.longs and not in context.shorts and data.can_trade(security):
            weights[security] = 0
    
    for security in context.longs:
        weights[security] = long_weight
    
    for security in context.shorts:
        weights[security] = short_weight
    
    return weights

def before_trading_start(context, data):
    
    pipe_results = pipeline_output('my_pipeline')
    
    context.longs= []
    for sec in pipe_results[pipe_results['longs']].index.tolist():
        if data.can_trade(sec):
            context.longs.append(sec)
            
    context.shorts= []
    for sec in pipe_results[pipe_results['shorts']].index.tolist():
        if data.can_trade(sec):
            context.shorts.append(sec)
            
def my_rebalance(context, data):
    
    target_weights = compute_target_weights(context, data)
    
    if target_weights:
        order_optimal_portfolio(
            objective = opt.TargetWeights(target_weights),
            constraints = [],
            )
    

