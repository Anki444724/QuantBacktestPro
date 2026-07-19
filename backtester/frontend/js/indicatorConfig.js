const INDICATOR_CONFIG = {

    SMA: {
        displayName: "Simple Moving Average",
        outputs: ["sma"],
        defaults: {
            period: 20
        },
        params: [
            {
                key: "period",
                label: "Period",
                type: "number",
                min: 1
            }
        ]
    },

    EMA: {
        displayName: "Exponential Moving Average",
        outputs: ["ema"],
        defaults: {
            period: 20
        },
        params: [
            {
                key: "period",
                label: "Period",
                type: "number",
                min: 1
            }
        ]
    },

    RSI: {
        displayName: "Relative Strength Index",
        outputs: ["rsi"],
        defaults: {
            period: 14
        },
        params: [
            {
                key: "period",
                label: "Period",
                type: "number",
                min: 1
            }
        ]
    },

    ATR: {
        displayName: "Average True Range",
        outputs: ["atr"],
        defaults: {
            period: 14
        },
        params: [
            {
                key: "period",
                label: "Period",
                type: "number",
                min: 1
            }
        ]
    }

};